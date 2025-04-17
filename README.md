# Solana wallet balance watcher for Raspberry Pi Pico with E-ink display

![img.png](images/img1.png)

Python script for monitoring balance of selected Solana wallet and its current market price. Graph of last 24 hour price is displayed on eInk display together with total wallet value (SOL only, value of other mints in the wallet are not calculated)

### Hardware

- **Raspberry Pico W**

- **Waveshare Pico-ePaper 2.9"** (**296***x***128**)

Every 15 minutes values are fetched and plot is updated with the latest price. Connection to Wi-Fi is required.

![img.png](images/img2.png)