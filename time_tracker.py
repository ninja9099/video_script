import time
import os

try:
    import ntplib
    client = ntplib.NTPClient()
    response = client.request('pool.ntp.org')
    print response
    os.system('date ' + time.strftime('%m%d%H%M%Y.%S',time.localtime(response.tx_time)))
except Exception as e:
    print (e)
    print('Could not sync with time server.')

print('Done.')
