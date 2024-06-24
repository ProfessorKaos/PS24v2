

def connectToWifiAndUpdate():
    import time, machine, network, gc, secrets
    import app._atcp as _atcp
#     import secrets
    
    time.sleep(1)
    print('Memory free', gc.mem_free())

    from app.ota_updater import OTAUpdater
    
    atcp = _atcp.ATCP(secrets.mDNS)
    

    token='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'
    otaUpdater = OTAUpdater('https://github.com/ProfessorKaos/PS24v2', headers={'Authorization': 'token {}'.format(token)}, main_dir='app')
    hasUpdated = otaUpdater.install_update_if_available()
    if hasUpdated:
        machine.reset()
    else:
        del(otaUpdater)
        gc.collect()
        

def startApp():
    import app.start


# check_updated()

# connectToWifiAndUpdate()

try: 
    startApp()
    
except Exception as e:
    print("Unable to start app, trying to download updated version")
    connectToWifiAndUpdate()
    machine.reset()