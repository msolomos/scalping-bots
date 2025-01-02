#!/bin/bash

# Τίτλος
echo "==========================="
echo "ATTENTION: UPLOADING BOT FILES TO KAGKAS SERVER"
echo "==========================="

# Επιβεβαίωση από τον χρήστη
read -p "Do you want to proceed with the upload? (yes/no): " user_confirmation

# Έλεγχος απάντησης
if [[ "$user_confirmation" != "yes" ]]; then
    echo "Upload canceled by user."
    exit 0
fi

# Ορισμός μεταβλητών
SFTP_USER="root"
SFTP_HOST="192.168.1.39"
SFTP_PORT=2244
FILES_TO_UPLOAD=(
    "/z/bots/scalping-bot/AVAX/scalper_avax.py:/opt/python/scalping-bot/AVAX"
	"/z/bots/scalping-bot/SOLANA/scalper_solana.py:/opt/python/scalping-bot/SOLANA"
	"/z/bots/scalping-bot/LITECOIN/scalper_litecoin.py:/opt/python/scalping-bot/LITECOIN"
	"/z/bots/scalping-bot/ETHEREUM/scalper_ethereum.py:/opt/python/scalping-bot/ETHEREUM"
	"/z/bots/scalping-bot/BITCOIN/scalper_bitcoin.py:/opt/python/scalping-bot/BITCOIN"
    "/z/bots/scalping-bot/XRP/scalper_xrp.py:/opt/python/scalping-bot/XRP"
	"/z/bots/scalping-bot/CARDANO/scalper_ada.py:/opt/python/scalping-bot/CARDANO"
    "/z/bots/scalping-bot/POLKADOT/scalper_dot.py:/opt/python/scalping-bot/POLKADOT"
	"/z/bots/scalping-bot/DOGECOIN/scalper_dogecoin.py:/opt/python/scalping-bot/DOGECOIN"
	"/z/bots/scalping-bot/POLYGON/scalper_polygon.py:/opt/python/scalping-bot/POLYGON"
	"/z/bots/scalping-bot/STELLAR/scalper_stellar.py:/opt/python/scalping-bot/STELLAR"

)

# Εκτέλεση SFTP
sftp -P $SFTP_PORT $SFTP_USER@$SFTP_HOST <<EOF
$(for file_mapping in "${FILES_TO_UPLOAD[@]}"; do
    local_file=$(echo $file_mapping | cut -d':' -f1)
    remote_path=$(echo $file_mapping | cut -d':' -f2)
    echo "cd $remote_path"
    echo "put $local_file"
done)
bye
EOF

echo "All files uploaded successfully!"
