import streamlit as st
import pandas as pd 
import numpy as np
import datetime
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

from transform import prep 

data = prep('mora.csv','cashflow.csv')

