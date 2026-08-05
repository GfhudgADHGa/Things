# neuralnet

A feedforward neural network from scratch: dense layers, activations,
backpropagation, and SGD — pure Python, no numpy, consistent with the
rest of this repo. The correctness proof isn't "it trained and the loss
went down" (that can look right while the gradient math is subtly wrong)
— it's **numerical gradient checking**, the standard technique for
verifying a backprop implementation independently of trusting the
calculus was transcribed correctly.

```bash
python3 main.py --task circle --output boundary.png
```

| `circle` | `xor_blobs` |
|---|---|
| ![circle decision boundary](examples/circle.png) | ![xor blobs decision boundary](examples/xor_blobs.png) |

Trained on 300 random 2D points; yellow/black dots are the two classes,
background color is the network's continuous confidence. Both converge
reliably (299/300 and 291/300 training accuracy in the committed
examples).

## The correctness proof: gradient checking

For each individual weight, nudge it by `+epsilon`, measure how much the
loss actually changes, nudge by `-epsilon`, measure again — the
finite-difference `(loss_plus - loss_minus) / (2*epsilon)` is a direct,
independent estimate of `dLoss/dWeight` that never looks at `backward()`
at all. Compare that against what `backward()` claims the gradient is.
If a real bug exists — a transposed index, a missing chain-rule term, a
sign flip — the two numbers disagree, often by orders of magnitude. If
the implementation is correct, they agree to several significant figures
(limited only by floating-point precision and the choice of epsilon).

`gradcheck.py` does exactly this, across every weight and bias in a
network. Measured on a 4-layer network mixing tanh/ReLU/sigmoid
activations against both loss functions: max relative error **~2.7e-9**
— essentially machine-precision noise, not "close enough to be
suspicious." `tests/test_gradcheck.py` runs this check across single
layers, deep mixed-activation networks, both loss functions, and 10
randomly-generated architectures — and includes one test that
deliberately breaks a gradient (adds `10.0` to every weight gradient) to
confirm the checker actually *notices* when something's wrong, not just
that it always reports success.

## Architecture

```
neuralnet/
  activations.py    sigmoid (numerically stable for large |x|), relu,
                       tanh, linear -- each paired with its derivative
                       expressed in terms of its own output
  layer.py            Dense: forward + a pure backward() (computes
                        gradients without mutating weights, which is
                        exactly what makes gradient checking possible)
                        + a separate apply_gradients() for the actual
                        SGD step
  losses.py            MSE, binary cross-entropy (with epsilon-clipped
                          log to avoid log(0))
  network.py            Sequential: chains layers, train_step/train_epoch
  gradcheck.py            the correctness proof described above
```

Splitting `backward()` (pure gradient computation) from
`apply_gradients()` (the mutating SGD step) is what makes gradient
checking possible at all: you need to compute a gradient, then perturb
that exact same weight and remeasure, without the act of computing the
gradient having already changed the weight.

## An honest negative result — and a partial fix

`main.py --task spiral` trains against two interleaved spirals — a
classic hard case for plain SGD on a small network. With plain SGD it
does **not** reliably converge: training accuracy sits at ~50%
(equivalent to random guessing on a balanced binary task) even with a
wider network and 2,000 epochs, confirmed reproducibly across runs. This
isn't a bug — tightly-wound spirals are a well-known stress case used in
ML pedagogy specifically to motivate why plain vanilla SGD on a small
MLP isn't enough in general.

`--momentum` was added afterward specifically to test whether the
standard fix (classic momentum SGD: `v = momentum*v - lr*grad; w += v`,
implemented in `Dense.apply_gradients` and threaded through
`Sequential.train_step`/`train_epoch`) actually addresses this. It
**helps substantially but doesn't fully solve it**: with a wider network
(32 hidden units per layer instead of 16/12), `learning_rate=0.02`,
`momentum=0.9`, accuracy climbs from the ~50% random-guessing floor to
the **70-87%** range over a few thousand epochs, but the loss curve
plateaus with visible oscillation rather than converging cleanly to
~100%. Tuning momentum without lowering the learning rate to compensate
made things *worse*, not better — one run with `learning_rate=0.05,
momentum=0.9` got stuck completely flat, a reminder that momentum
amplifies whatever learning rate you give it, for better or worse, and
isn't a substitute for tuning both together. The honest reading: this
is real, measured progress from a real (if standard) technique, not a
solved problem — getting the rest of the way to full convergence is left
as one of the possible expansions below rather than something chased to
completion here. No committed example image for `spiral`, since neither
version reliably produces a boundary worth showing — but the task and
`--momentum` flag are both there to try, and this note exists so both
outcomes read as documented, not silently dropped.

## Usage

```bash
python3 main.py --task circle --seed 1 --epochs 400 --output boundary.png
```

| Flag | Meaning |
|---|---|
| `--task` | `circle`, `xor_blobs`, or `spiral` (see above) |
| `--seed` | RNG seed for both the dataset and initial weights |
| `--epochs` / `--learning-rate` / `--momentum` | training hyperparameters (`--momentum 0` is plain SGD, the default) |
| `--output` | output PNG path for the decision-boundary visualization |

Or as a library:

```python
import random
from neuralnet import Dense, Sequential, TANH, SIGMOID, MSE

rng = random.Random(0)
net = Sequential([Dense(2, 8, TANH, rng), Dense(8, 1, SIGMOID, rng)])
for _ in range(3000):
    net.train_step([0.0, 1.0], [1.0], MSE, learning_rate=0.5)
```

The core library (`activations.py` through `gradcheck.py`) has zero
dependencies. `main.py`'s decision-boundary visualization uses Pillow —
a demo/rendering concern, not the neural network itself.

## Tests

```bash
pip install -r requirements.txt
python3 -m pytest
```

50 tests: activation functions (including that sigmoid doesn't overflow
on extreme inputs), layer forward/backward mechanics (backward provably
doesn't mutate weights, `apply_gradients` moves weights by exactly
`-lr * gradient` with momentum=0, and with momentum>0 the velocity
accumulates across calls exactly as hand-computed), loss functions,
network training (a single example's loss provably decreases with and
without momentum, XOR is learned to 100% accuracy, zero learning rate
leaves weights unchanged), and the gradient-checking suite described
above.

## Possible expansions

- Adam (adaptive per-parameter learning rates) or further momentum/
  learning-rate tuning to close the remaining gap on the spiral task
- Softmax + categorical cross-entropy for multi-class classification
- Mini-batching (currently pure online/stochastic, one example at a time)
- Convolutional layers
