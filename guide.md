# Client SDK guide

## Installation
- ### create venv
	`python3 -m venv ~/venv`
- ### Install with pip
	```
	source ~/venv/bin/activate

	python3 -m pip install projectaria_client_sdk --no-cache-dir
	```


## Pairing + SETUP client sdk
- ### For problems run
	`aria-doctor`
- ### Pairing
	`aria auth pair`

## Code examples

### Connection
- `python -m device_connect`
: gives device's info (battery level, wifi ssid)
- to connect via wifi :`python -m device_connect --device-ip DEVICEIP` : DEIVCEIP is found in companion app tapping over wifi symbol in dashboard

### Recording
#### Start and stop recording over Wi-Fi

`python -m device_record --device-ip <Glasses IP>`

#### Start and stop recording using a custom sensor profile


`python -m device_record --profile profileN --device-ip <Glasses IP>`

#### show recordings 
`adb shell ls -l /sdcard/recording`

#### Transfer specific file
`adb pull /sdcard/recording/myVrsFile.vrs myLocalFolder/`

#### Transfer file metadata
` adb pull /sdcard/recording/myVrsFile.json myLocalFolder/`
### Visualizing data recordings
`viewer_aria_sensors --vrs $MPS_SAMPLE_PATH/sample.vrs`

### Streaming

#### Streaming start over wifi
`aria streaming start --interface wifi --device-ip DEVICEIP --use-ephemeral-certs`

#### Steaming with hotspot mode 
- `aria streaming start --interface hotspot --use-ephemeral-certs`
- connect to wifi using info displayed
- run `python -m streaming_subscribe --update_iptables`

### Stream and visualize all data
`python -m device_stream --interface wifi --device-ip <Glasses IP> --update_iptables`





