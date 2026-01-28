# ===============================
# Automated Portfolio Report
# ===============================

import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mtick
import smtplib
from email.message import EmailMessage

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
)
from PIL import Image as PILImage
