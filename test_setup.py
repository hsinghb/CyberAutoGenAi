"""Test the setup by importing all required packages."""
import sys
import os
import xgboost
import flaml
import autogen
import streamlit
import numpy
import pandas
import scipy
import sklearn

def test_imports():
    """Test all imports and print versions."""
    print(f"Python version: {sys.version}")
    print(f"XGBoost version: {xgboost.__version__}")
    print(f"FLAML version: {flaml.__version__}")
    print(f"AutoGen version: {autogen.__version__}")
    print(f"Streamlit version: {streamlit.__version__}")
    print(f"NumPy version: {numpy.__version__}")
    print(f"Pandas version: {pandas.__version__}")
    print(f"SciPy version: {scipy.__version__}")
    print(f"Scikit-learn version: {sklearn.__version__}")
    
    # Test XGBoost functionality
    print("\nTesting XGBoost functionality...")
    import numpy as np
    data = np.random.rand(5, 3)
    label = np.random.randint(2, size=5)
    dtrain = xgboost.DMatrix(data, label=label)
    param = {'max_depth': 2, 'eta': 1, 'objective': 'binary:logistic'}
    bst = xgboost.train(param, dtrain, 1)
    print("XGBoost test successful!")

if __name__ == "__main__":
    test_imports()
