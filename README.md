# AI-Enhanced Cryptocurrency Trading Bot

## Overview

This project is a cryptocurrency trading bot that uses simple moving average (SMA) crossover strategy to make trading decisions. It's designed as a foundation for more advanced algorithmic trading strategies, with the ultimate goal of incorporating artificial intelligence (AI) to enhance trading performance.

## Current Features

- Connects to Binance API for real-time cryptocurrency data
- Implements a basic SMA crossover strategy
- Executes market orders based on generated signals
- Robust error handling and logging

## Future AI Integration Goals

While the current version uses a simple moving average strategy, our higher goal is to evolve this bot into an AI-powered trading system. Future enhancements may include:

1. Machine Learning models for price prediction
2. Natural Language Processing (NLP) for sentiment analysis of crypto news
3. Reinforcement Learning for dynamic strategy optimization
4. Deep Learning for pattern recognition in price charts

## Installation

1. Clone this repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with your Binance API credentials and trading parameters:
   ```bash
   API_KEY=your_api_key
   API_SECRET=your_api_secret
   SYMBOL=BTCUSDT
   TRADE_QUANTITY=0.001
   SHORT_WINDOW=20
   LONG_WINDOW=50
   INTERVAL=1h
   LOOKBACK=100h
   ```

## Usage

Run the bot with:

```
python src/main.py
```

## Disclaimer

This bot is for educational purposes only. Cryptocurrency trading carries a high level of risk, and may not be suitable for all investors. Please use this code