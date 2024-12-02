#!/bin/bash

# Start Apache
service apache2 start

# Start SSH
service ssh start

# Keep the container running by tailing the logs or keeping the shell open
tail -f /dev/null
