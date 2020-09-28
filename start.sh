export PATH=$PATH:/home/pi/venv/bin:/usr/kerberos/sbin:/usr/kerberos/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# source /home/pi/venv/bin/activate
alias  chdir="cd /home/pi/playercake"
/home/pi/venv/bin/python3 /home/pi/playercake/ux.py && XAUTHORITY=/run/user/120/gdm/XAuthority xrandr -d :0 --output HDMI-1 --rotate right