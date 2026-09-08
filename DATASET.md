# Dataset

## Fake and Real News Dataset

This project uses the Fake and Real News Dataset for training and evaluating the fake news classification model.

### Files

The dataset contains:

- `Fake.csv`
- `True.csv`

### Dataset Statistics

| Dataset | Articles |
|---|---:|
| Fake News | 23,481 |
| Real News | 21,417 |
| Total | 44,898 |

The initial analysis found 209 duplicate rows.

### Dataset Location

The CSV files should be placed locally at:

```text
data/raw/
├── Fake.csv
└── True.csv