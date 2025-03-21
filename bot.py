
import ccxt
import pandas as pd
import time
from datetime import datetime
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration
sender = "dahmadu071@gmail.com"
recipients = ["teejeedeeone@gmail.com"]
password = "oase wivf hvqn lyhr"

# Function to send an email
def send_email(subject, body):
    try:
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender, password)  # Log in to the email account
            server.sendmail(sender, recipients, msg.as_string())  # Send the email
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Initialize the exchange
exchange = ccxt.bitget()

# List of crypto pairs to check
symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'XRP/USDT:USDT', 'EOS/USDT:USDT', 'BCH/USDT:USDT', 'LTC/USDT:USDT', 'ADA/USDT:USDT', 'ETC/USDT:USDT', 'LINK/USDT:USDT', 'TRX/USDT:USDT', 'DOT/USDT:USDT', 'DOGE/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT', 'UNI/USDT:USDT', 'ICP/USDT:USDT', 'AAVE/USDT:USDT', 'FIL/USDT:USDT', 'XLM/USDT:USDT', 'ATOM/USDT:USDT', 'XTZ/USDT:USDT', 'SUSHI/USDT:USDT', 'AXS/USDT:USDT', 'THETA/USDT:USDT', 'AVAX/USDT:USDT', 'SHIB/USDT:USDT', 'MANA/USDT:USDT', 'GALA/USDT:USDT', 'SAND/USDT:USDT', 'DYDX/USDT:USDT', 'CRV/USDT:USDT', 'NEAR/USDT:USDT', 'EGLD/USDT:USDT', 'KSM/USDT:USDT', 'AR/USDT:USDT', 'PEOPLE/USDT:USDT', 'LRC/USDT:USDT', 'NEO/USDT:USDT', 'ALICE/USDT:USDT', 'WAVES/USDT:USDT', 'ALGO/USDT:USDT', 'IOTA/USDT:USDT', 'ENJ/USDT:USDT', 'GMT/USDT:USDT', 'ZIL/USDT:USDT', 'IOST/USDT:USDT', 'APE/USDT:USDT', 'RUNE/USDT:USDT', 'KNC/USDT:USDT', 'APT/USDT:USDT', 'CHZ/USDT:USDT', 'ROSE/USDT:USDT', 'ZRX/USDT:USDT', 'KAVA/USDT:USDT', 'ENS/USDT:USDT', 'MTL/USDT:USDT', 'AUDIO/USDT:USDT', 'SXP/USDT:USDT', 'C98/USDT:USDT', 'OP/USDT:USDT', 'RSR/USDT:USDT', 'SNX/USDT:USDT', 'STORJ/USDT:USDT', '1INCH/USDT:USDT', 'COMP/USDT:USDT', 'IMX/USDT:USDT', 'LUNA/USDT:USDT', 'FLOW/USDT:USDT', 'TRB/USDT:USDT', 'QTUM/USDT:USDT', 'API3/USDT:USDT', 'MASK/USDT:USDT', 'WOO/USDT:USDT', 'GRT/USDT:USDT', 'BAND/USDT:USDT', 'STG/USDT:USDT', 'LUNC/USDT:USDT', 'ONE/USDT:USDT', 'JASMY/USDT:USDT', 'MKR/USDT:USDT', 'BAT/USDT:USDT', 'MAGIC/USDT:USDT', 'ALPHA/USDT:USDT', 'LDO/USDT:USDT', 'CELO/USDT:USDT', 'BLUR/USDT:USDT', 'MINA/USDT:USDT', 'CORE/USDT:USDT', 'CFX/USDT:USDT', 'ASTR/USDT:USDT', 'GMX/USDT:USDT', 'ANKR/USDT:USDT', 'ACH/USDT:USDT', 'FET/USDT:USDT', 'FXS/USDT:USDT', 'HOOK/USDT:USDT', 'SSV/USDT:USDT', 'USDC/USDT:USDT', 'LQTY/USDT:USDT', 'STX/USDT:USDT', 'TRU/USDT:USDT', 'HBAR/USDT:USDT', 'INJ/USDT:USDT', 'BEL/USDT:USDT', 'COTI/USDT:USDT', 'VET/USDT:USDT', 'ARB/USDT:USDT', 'LOOKS/USDT:USDT', 'KAIA/USDT:USDT', 'FLM/USDT:USDT', 'CKB/USDT:USDT', 'ID/USDT:USDT', 'JOE/USDT:USDT', 'TLM/USDT:USDT', 'HOT/USDT:USDT', 'CHR/USDT:USDT', 'RDNT/USDT:USDT', 'ICX/USDT:USDT', 'ONT/USDT:USDT', 'NKN/USDT:USDT', 'ARPA/USDT:USDT', 'SFP/USDT:USDT', 'CTSI/USDT:USDT', 'SKL/USDT:USDT', 'RVN/USDT:USDT', 'CELR/USDT:USDT', 'FLOKI/USDT:USDT', 'SPELL/USDT:USDT', 'SUI/USDT:USDT', 'PEPE/USDT:USDT', 'IOTX/USDT:USDT', 'UMA/USDT:USDT', 'TURBO/USDT:USDT', 'BSV/USDT:USDT', 'TON/USDT:USDT', 'GTC/USDT:USDT', 'DENT/USDT:USDT', 'ZEN/USDT:USDT', 'PHB/USDT:USDT', 'ORDI/USDT:USDT', '1000BONK/USDT:USDT', 'LEVER/USDT:USDT', 'USTC/USDT:USDT', 'RAD/USDT:USDT', 'QNT/USDT:USDT', 'MAV/USDT:USDT', 'XVG/USDT:USDT', '1000XEC/USDT:USDT', 'AGLD/USDT:USDT', 'WLD/USDT:USDT', 'PENDLE/USDT:USDT', 'ARKM/USDT:USDT', 'CVX/USDT:USDT', 'YGG/USDT:USDT', 'OGN/USDT:USDT', 'LPT/USDT:USDT', 'BNT/USDT:USDT', 'SEI/USDT:USDT', 'CYBER/USDT:USDT', 'BAKE/USDT:USDT', 'BIGTIME/USDT:USDT', 'WAXP/USDT:USDT', 'POLYX/USDT:USDT', 'TIA/USDT:USDT', 'MEME/USDT:USDT', 'PYTH/USDT:USDT', 'JTO/USDT:USDT', '1000SATS/USDT:USDT', '1000RATS/USDT:USDT', 'ACE/USDT:USDT', 'XAI/USDT:USDT', 'MANTA/USDT:USDT', 'ALT/USDT:USDT', 'JUP/USDT:USDT', 'ZETA/USDT:USDT', 'STRK/USDT:USDT', 'PIXEL/USDT:USDT', 'DYM/USDT:USDT', 'WIF/USDT:USDT', 'AXL/USDT:USDT', 'BEAM/USDT:USDT', 'BOME/USDT:USDT', 'METIS/USDT:USDT', 'NFP/USDT:USDT', 'VANRY/USDT:USDT', 'AEVO/USDT:USDT', 'ETHFI/USDT:USDT', 'OM/USDT:USDT', 'ONDO/USDT:USDT', 'CAKE/USDT:USDT', 'PORTAL/USDT:USDT', 'NTRN/USDT:USDT', 'KAS/USDT:USDT', 'AI/USDT:USDT', 'ENA/USDT:USDT', 'W/USDT:USDT', 'CVC/USDT:USDT', 'TNSR/USDT:USDT', 'SAGA/USDT:USDT', 'TAO/USDT:USDT', 'RAY/USDT:USDT', 'ATA/USDT:USDT', 'SUPER/USDT:USDT', 'ONG/USDT:USDT', 'OMNI1/USDT:USDT', 'LSK/USDT:USDT', 'GLM/USDT:USDT', 'REZ/USDT:USDT', 'XVS/USDT:USDT', 'MOVR/USDT:USDT', 'BB/USDT:USDT', 'NOT/USDT:USDT', 'BICO/USDT:USDT', 'HIFI/USDT:USDT', 'IO/USDT:USDT', 'TAIKO/USDT:USDT', 'BRETT/USDT:USDT', 'ATH/USDT:USDT', 'ZK/USDT:USDT', 'MEW/USDT:USDT', 'LISTA/USDT:USDT', 'ZRO/USDT:USDT', 'BLAST/USDT:USDT', 'DOG/USDT:USDT', 'PAXG/USDT:USDT', 'ZKJ/USDT:USDT', 'BGB/USDT:USDT', 'MOCA/USDT:USDT', 'GAS/USDT:USDT', 'UXLINK/USDT:USDT', 'BANANA/USDT:USDT', 'MYRO/USDT:USDT', 'POPCAT/USDT:USDT', 'PRCL/USDT:USDT', 'CLOUD/USDT:USDT', 'AVAIL/USDT:USDT', 'RENDER/USDT:USDT', 'RARE/USDT:USDT', 'PONKE/USDT:USDT', 'MAX/USDT:USDT', 'T/USDT:USDT', '1000000MOG/USDT:USDT', 'G/USDT:USDT', 'SYN/USDT:USDT', 'SYS/USDT:USDT', 'VOXEL/USDT:USDT', 'ALPACA/USDT:USDT', 'SUN/USDT:USDT', 'VIDT/USDT:USDT', 'DOGS/USDT:USDT', 'NULS/USDT:USDT', 'ORDER/USDT:USDT', 'SUNDOG/USDT:USDT', 'AKT/USDT:USDT', 'MBOX/USDT:USDT', 'HNT/USDT:USDT', 'CHESS/USDT:USDT', 'FLUX/USDT:USDT', 'POL/USDT:USDT', 'BSW/USDT:USDT', 'NEIROETH/USDT:USDT', 'RPL/USDT:USDT', 'QUICK/USDT:USDT', 'AERGO/USDT:USDT', '1MBABYDOGE/USDT:USDT', '1000CAT/USDT:USDT', 'KDA/USDT:USDT', 'FIDA/USDT:USDT', 'CATI/USDT:USDT', 'FIO/USDT:USDT', 'ARK/USDT:USDT', 'GHST/USDT:USDT', 'LOKA/USDT:USDT', 'VELO/USDT:USDT', 'HMSTR/USDT:USDT', 'AGI/USDT:USDT', 'REI/USDT:USDT', 'COS/USDT:USDT', 'EIGEN/USDT:USDT', 'MOODENG/USDT:USDT', 'DIA/USDT:USDT', 'FTN/USDT:USDT', 'OG/USDT:USDT', 'NEIROCTO/USDT:USDT', 'ETHW/USDT:USDT', 'DegenReborn/USDT:USDT', 'KMNO/USDT:USDT', 'POWR/USDT:USDT', 'PYR/USDT:USDT', 'CARV/USDT:USDT', 'SLERF/USDT:USDT', 'PUFFER/USDT:USDT', '10000WHY/USDT:USDT', 'DEEP/USDT:USDT', 'DBR/USDT:USDT', 'LUMIA/USDT:USDT', 'SCR/USDT:USDT', 'GOAT/USDT:USDT', 'X/USDT:USDT', 'SAFE/USDT:USDT', 'GRASS/USDT:USDT', 'SWEAT/USDT:USDT', 'SANTOS/USDT:USDT', 'SPX/USDT:USDT', 'TROY/USDT:USDT', 'VIRTUAL/USDT:USDT', 'AERO/USDT:USDT', 'CETUS/USDT:USDT', 'COW/USDT:USDT', 'SWELL/USDT:USDT', 'DRIFT/USDT:USDT', 'PNUT/USDT:USDT', 'ACT/USDT:USDT', 'CRO/USDT:USDT', 'PEAQ/USDT:USDT', 'FOXY/USDT:USDT', 'FWOG/USDT:USDT', 'HIPPO/USDT:USDT', 'SNT/USDT:USDT', 'MERL/USDT:USDT', 'STEEM/USDT:USDT', 'PROS/USDT:USDT', 'BAN/USDT:USDT', 'OL/USDT:USDT', 'MORPHO/USDT:USDT', 'SCRT/USDT:USDT', 'CHILLGUY/USDT:USDT', 'MEMEFI/USDT:USDT', '1MCHEEMS/USDT:USDT', 'OXT/USDT:USDT', 'ZRC/USDT:USDT', 'THE/USDT:USDT', 'MAJOR/USDT:USDT', 'CTC/USDT:USDT', 'XDC/USDT:USDT', 'XION/USDT:USDT', 'ORCA/USDT:USDT', 'ACX/USDT:USDT', 'NS/USDT:USDT', 'MOVE/USDT:USDT', 'KOMA/USDT:USDT', 'ME/USDT:USDT', 'VELODROME/USDT:USDT', 'AVA/USDT:USDT', 'VANA/USDT:USDT', 'HYPE/USDT:USDT', 'PENGU/USDT:USDT', 'USUAL/USDT:USDT', 'FUEL/USDT:USDT', 'CGPT/USDT:USDT', 'AIXBT/USDT:USDT', 'FARTCOIN/USDT:USDT', 'HIVE/USDT:USDT', 'DEXE/USDT:USDT', 'GIGA/USDT:USDT', 'PHA/USDT:USDT', 'DF/USDT:USDT', 'AI16Z/USDT:USDT', 'GRIFFAIN/USDT:USDT', 'ZEREBRO/USDT:USDT', 'BIO/USDT:USDT', 'SWARMS/USDT:USDT', 'ALCH/USDT:USDT', 'COOKIE/USDT:USDT', 'SONIC/USDT:USDT', 'AVAAI/USDT:USDT', 'S/USDT:USDT', 'PROM/USDT:USDT', 'DUCK/USDT:USDT', 'BGSC/USDT:USDT', 'SOLV/USDT:USDT', 'ARC/USDT:USDT', 'NC/USDT:USDT', 'PIPPIN/USDT:USDT', 'TRUMP/USDT:USDT', 'MELANIA/USDT:USDT', 'PLUME/USDT:USDT', 'VTHO/USDT:USDT', 'J/USDT:USDT', 'QKC/USDT:USDT', 'VINE/USDT:USDT', 'ANIME/USDT:USDT', 'STPT/USDT:USDT', 'XCN/USDT:USDT', 'TOSHI/USDT:USDT', 'VVV/USDT:USDT', 'JELLYJELLY/USDT:USDT', 'FORTH/USDT:USDT', 'LUCE/USDT:USDT', 'BERA/USDT:USDT', 'TSTBSC/USDT:USDT', '10000ELON/USDT:USDT', 'LAYER/USDT:USDT', 'B3/USDT:USDT', 'IP/USDT:USDT', 'RON/USDT:USDT', 'HEI/USDT:USDT', 'SHELL/USDT:USDT', 'BURGER/USDT:USDT', 'BROCCOLI/USDT:USDT', 'JAILSTOOL/USDT:USDT', 'AUCTION/USDT:USDT', 'GPS/USDT:USDT', 'GNO/USDT:USDT', 'AIOZ/USDT:USDT', 'PI/USDT:USDT', 'AVL/USDT:USDT', 'KAITO/USDT:USDT', 'GODS/USDT:USDT', 'ROAM/USDT:USDT', 'RED/USDT:USDT', 'ELX/USDT:USDT', 'SERAPH/USDT:USDT', 'BMT/USDT:USDT', 'OIK/USDT:USDT', 'VIC/USDT:USDT', 'EPIC/USDT:USDT', 'OBT/USDT:USDT', 'MUBARAK/USDT:USDT', 'NMR/USDT:USDT', 'TUT/USDT:USDT', 'FORM/USDT:USDT', 'RSS3/USDT:USDT', 'BID/USDT:USDT', 'SIREN/USDT:USDT', 'BROCCOLIF3B/USDT:USDT', 'BANANAS31/USDT:USDT', 'BR/USDT:USDT']

# Function to fetch OHLCV data and calculate Donchian Channels with offset
def check_donchian_channel(symbol):
    # Fetch OHLCV data
    timeframe = '15m'
    limit = 100  # Fetch the most recent 100 data points
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')

    # Convert timestamps to Africa/Lagos timezone
    lagos_tz = pytz.timezone('Africa/Lagos')
    data['timestamp'] = data['timestamp'].dt.tz_localize('UTC').dt.tz_convert(lagos_tz)

    # Parameters
    length = 20  # Donchian Channel length
    offset = -7   # Offset for Donchian Channel calculation

    # Calculate Donchian Channel values with offset
    lower = data['low'].shift(offset).rolling(window=length).min()  # Lowest low over the period, shifted by offset
    upper = data['high'].shift(offset).rolling(window=length).max()  # Highest high over the period, shifted by offset

    # Get the 15th last candle's high, low, close, and timestamp
    candle_index = -26  # 15th last candle
    candle_high = data['high'].iloc[candle_index]
    candle_low = data['low'].iloc[candle_index]
    candle_close = data['close'].iloc[candle_index]
    candle_timestamp = data['timestamp'].iloc[candle_index]
    candle_upper = upper.iloc[candle_index]
    candle_lower = lower.iloc[candle_index]

    # Check if the candle's lower wick touches the lower Donchian band
    if candle_low <= candle_lower:
        message = f'{symbol} touched the Lower Donchian Channel (with offset {offset}) at price: {candle_lower} on {candle_timestamp.strftime("%Y-%m-%d %H:%M:%S")} (Africa/Lagos)'
        print(message)
        send_email(f"{symbol} - Lower Donchian Channel Touched", message)

    # Check if the candle's upper wick touches the upper Donchian band
    if candle_high >= candle_upper:
        message = f'{symbol} touched the Upper Donchian Channel (with offset {offset}) at price: {candle_upper} on {candle_timestamp.strftime("%Y-%m-%d %H:%M:%S")} (Africa/Lagos)'
        print(message)
        send_email(f"{symbol} - Upper Donchian Channel Touched", message)

    # If neither band is touched
    if candle_low > candle_lower and candle_high < candle_upper:
        message = f'{symbol} did not touch either band (with offset {offset}) on {candle_timestamp.strftime("%Y-%m-%d %H:%M:%S")} (Africa/Lagos).'
        print(message)

# Loop through each symbol and check Donchian Channels
for symbol in symbols:
    check_donchian_channel(symbol)
    time.sleep(0)  # No delay between each pair
