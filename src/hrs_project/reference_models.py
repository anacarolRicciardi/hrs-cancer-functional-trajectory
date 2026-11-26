"""Referências preditivas iniciais: ajuste só no treino, sem ler teste."""
import warnings
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import roc_auc_score,average_precision_score,brier_score_loss,log_loss
from .integrated_panel import feature_columns


def align_xy(x,y):
    keys=['id','wave']
    for frame in [x,y]:
        if frame[keys].isna().any().any() or frame.duplicated(keys).any():
            raise ValueError('Chaves pessoa–onda ausentes ou duplicadas')
    a=x.sort_values(keys).reset_index(drop=True)
    b=y.sort_values(keys).reset_index(drop=True)
    if not a[keys].equals(b[keys]):
        raise ValueError('X e y possuem chaves diferentes')
    if not b.target.isin([0,1]).all() or b.empty:
        raise ValueError('Alvo vazio, ausente ou não binário')
    values=a[feature_columns()].apply(pd.to_numeric,errors='raise').astype(float)
    if np.isinf(values.to_numpy()).any():
        raise ValueError('Atributos infinitos')
    return a[keys],values,b.target.astype(int)


def fit_references(x,y):
    if y.nunique()!=2:
        raise ValueError('Treino precisa de ambas as classes')
    # Colunas inteiramente ausentes são determinadas exclusivamente pelo treino.
    columns=x.columns[x.notna().any()].tolist()
    if not columns:
        raise ValueError('Todos os preditores estão ausentes no treino')
    model=Pipeline([('imputer',SimpleImputer(strategy='median',add_indicator=True)),
        ('scaler',StandardScaler()),
        ('logistic',LogisticRegression(C=1.0,max_iter=2000,solver='lbfgs'))])
    with warnings.catch_warnings():
        warnings.simplefilter('error',ConvergenceWarning)
        model.fit(x[columns],y)
    return {'model':model,'columns':columns,'prevalence':float(y.mean()),
            'dropped_all_missing':[c for c in x if c not in columns]}


def predict_references(fitted,x):
    return {'constant':np.full(len(x),fitted['prevalence']),
            'logistic':fitted['model'].predict_proba(x[fitted['columns']])[:,1]}


def probability_metrics(y,p):
    y=np.asarray(y); p=np.asarray(p,dtype=float)
    if y.ndim!=1 or p.ndim!=1 or len(y)!=len(p) or not len(y):
        raise ValueError('Vetores incompatíveis ou vazios')
    if not np.isin(y,[0,1]).all() or not np.isfinite(p).all() or ((p<0)|(p>1)).any():
        raise ValueError('Alvos ou probabilidades inválidos')
    two=len(np.unique(y))==2
    return dict(n=len(y),events=int(y.sum()),event_rate=float(y.mean()),
        mean_prediction=float(p.mean()),brier=brier_score_loss(y,p),
        log_loss=log_loss(y,p,labels=[0,1]),
        roc_auc=roc_auc_score(y,p) if two else np.nan,
        average_precision=average_precision_score(y,p) if two else np.nan)
