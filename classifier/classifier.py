from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd
import numpy as np
from xgboost import plot_importance
import matplotlib.pyplot as plt
# --- 1) Wczytanie ---
nodes_df = pd.read_csv("nodes_df.csv")
edges_df = pd.read_csv("edges_df.csv")
labels   = pd.read_csv("failure_labels.csv")   # zakładam kolumnę failure_label

# --- 2) Nadanie sekwencyjnych indeksów run_idx wg kolejności wierszy ---
n_runs = len(labels)

def add_sequential_run_idx(df, n_groups, colname="run_idx"):
    idx = np.arange(len(df))
    splits = np.array_split(idx, n_groups)            
    run_idx = np.empty(len(df), dtype=int)
    for i, part in enumerate(splits):
        run_idx[part] = i
    out = df.copy()
    out[colname] = run_idx
    return out

nodes_df = add_sequential_run_idx(nodes_df, n_runs, "run_idx")
edges_df = add_sequential_run_idx(edges_df, n_runs, "run_idx")
labels   = labels.copy()
labels["run_idx"] = np.arange(n_runs)   # też indeks sekwencyjny po kolei

# --- 3) Agregacja do 1 wiersza na run_idx ---
def aggregate_by_runidx(df, run_col="run_idx", how_num="mean", sum_prefixes=()):
    df = df.copy()
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if run_col not in num_cols:
        num_cols = [run_col] + num_cols
    use = df[num_cols]

    
    agg = {c: how_num for c in use.columns if c != run_col}

    
    to_sum = []
    for pref in sum_prefixes:
        to_sum += [c for c in use.columns if c.startswith(pref)]
    for c in to_sum:
        if c in agg:
            agg[c] = "sum"

    return use.groupby(run_col, as_index=False).agg(agg)


nodes_agg = aggregate_by_runidx(nodes_df, sum_prefixes=("type_", "status_"))
edges_agg = aggregate_by_runidx(edges_df, sum_prefixes=("layer_", "status_"))


nodes_agg = nodes_agg.add_prefix("nodes_").rename(columns={"nodes_run_idx": "run_idx"})
edges_agg = edges_agg.add_prefix("edges_").rename(columns={"edges_run_idx": "run_idx"})


feat = nodes_agg.merge(edges_agg, on="run_idx", how="inner")
data = feat.merge(labels[["run_idx", "failure_label"]], on="run_idx", how="inner")


X = data.drop(columns=["run_idx", "failure_label"], errors="ignore")
X = X.select_dtypes(include=[np.number]).copy()
y = data["failure_label"].astype(float)

print(f"X shape: {X.shape}, y shape: {y.shape}")


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

model = XGBRegressor(
    n_estimators=500,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, y_train)

# --- 7) Ewaluacja ---
pred = model.predict(X_test)
print("MSE:", mean_squared_error(y_test, pred))
print("R^2:", r2_score(y_test, pred))

# (opcjonalnie) ważności
imp = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
print("\nTop features:\n", imp.head(15))

plt.figure(figsize=(8, 6))
plot_importance(model, importance_type='gain', max_num_features=15)
plt.title("Feature Importances (Gain)")
plt.show()
