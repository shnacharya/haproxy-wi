import cgi
import os
import paramiko
import http.cookies
from paramiko import SSHClient
from datetime import datetime
from pytz import timezone
from configparser import ConfigParser, ExtendedInterpolation
import sql

path_config = "haproxy-webintarface.config"
config = ConfigParser(interpolation=ExtendedInterpolation())
config.read(path_config)

form = cgi.FieldStorage()
serv = form.getvalue('serv')
fullpath = config.get('main', 'fullpath')
log_path = config.get('main', 'log_path')
time_zone = config.get('main', 'time_zone')
ssh_keys = config.get('ssh', 'ssh_keys')
ssh_user_name = config.get('ssh', 'ssh_user_name')
haproxy_configs_server = config.get('configs', 'haproxy_configs_server')
hap_configs_dir = config.get('configs', 'haproxy_save_configs_dir')
haproxy_config_path  = config.get('haproxy', 'haproxy_config_path')
tmp_config_path = config.get('haproxy', 'tmp_config_path')
restart_command = config.get('haproxy', 'restart_command')

def check_config():
	for section in [ 'main', 'configs', 'ssh', 'logs', 'haproxy' ]:
		if not config.has_section(section):
			print('<b style="color: red">Check config file, no %s section</b>' % section)
			
def get_data(type):
	now_utc = datetime.now(timezone(time_zone))
	if type == 'config':
		fmt = "%Y-%m-%d.%H:%M:%S"
	if type == 'logs':
		fmt = '%Y%m%d'
	return now_utc.strftime(fmt)
			
def logging(serv, action):
	dateFormat = "%b  %d %H:%M:%S"
	now_utc = datetime.now(timezone(time_zone))
	IP = cgi.escape(os.environ["REMOTE_ADDR"])
	cookie = http.cookies.SimpleCookie(os.environ.get("HTTP_COOKIE"))
	login = cookie.get('login')
	mess = now_utc.strftime(dateFormat) + " from " + IP + " user: " + login.value + " " + action + " for: " + serv + "\n"
	log = open(log_path + "/config_edit-"+get_data('logs')+".log", "a")
	log.write(mess)
	log.close
	
	if config.get('telegram', 'enable') == "1": telegram_send_mess(mess)

def telegram_send_mess(mess):
	import telegram
	token_bot = config.get('telegram', 'token')
	channel_name = config.get('telegram', 'channel_name')
	proxy = config.get('telegram', 'proxy')
	
	if proxy is not None:
		pp = telegram.utils.request.Request(proxy_url=proxy)
	bot = telegram.Bot(token=token_bot, request=pp)
	bot.send_message(chat_id=channel_name, text=mess)
	
def check_login(**kwargs):
	cookie = http.cookies.SimpleCookie(os.environ.get("HTTP_COOKIE"))
	login = cookie.get('login')
	role = cookie.get('role')
	ref = os.environ.get("SCRIPT_NAME")

	if login is None:
		print('<meta http-equiv="refresh" content="0; url=login.py?ref=%s">' % ref)
				
def is_admin(**kwargs):
	cookie = http.cookies.SimpleCookie(os.environ.get("HTTP_COOKIE"))
	role = cookie.get('role')
	level = kwargs.get("level")
	
	if role is None:
		role = 3
	else:
		role = int(role.value)
		
	if level is None:
		level = 1
		
	try:
		if role <= level:
			return True
		else:
			return False
	except:
		return False
		pass

def page_for_admin(**kwargs):
	give_level = kwargs.get("level")
	
	if give_level is None:
		give_level = 1
	
	if not is_admin(level = give_level):
		print('<center><h3 style="color: red">How did you get here?! O_o You do not have need permissions</h>')
		print('<meta http-equiv="refresh" content="10; url=/">')
		import sys
		sys.exit()
		
def get_button(button, **kwargs):
	value = kwargs.get("value")
	if value is None:
		value = ""
	print('<button type="submit" value="%s" name="%s" class="btn btn-default">%s</button>' % (value, value, button))

def head(title):
	print('Content-type: text/html\n')
	print('<html><head><title>%s</title>' % title)
	print('<link href="/image/pic/favicon.ico" rel="icon" type="image/png" />'
		'<script>'
			'FontAwesomeConfig = { searchPseudoElements: true, observeMutations: false };'
		'</script>'
		'<script defer src="/inc/fa-solid.min.js"></script>'	
		'<script defer src="/inc/fontawesome.min.js"></script>'	
		'<meta charset="UTF-8">'		
		'<link href="/inc/awesome.css" rel="stylesheet">'
		'<link href="/inc/vertical_scrol/custom_scrollbar.css" rel="stylesheet">'
		'<link href="/inc/style.css" rel="stylesheet">'
		'<link href="/inc/nprogress.css" rel="stylesheet">'
		'<link rel="stylesheet" href="http://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">'
		'<script src="https://code.jquery.com/jquery-1.12.4.js"></script>'
		'<script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>'
		'<script src="/inc/js-cookie.js"></script>'
		'<script src="/inc/script.js"></script>'		
		'<script src="/inc/configshow.js"></script>'
		'<script src="/inc/nprogress.js"></script>'		
		'<script src="/inc/vertical_scrol/custom_scrollbar.min.js"></script>'		
		'</head>'
			'<body>'
				'<a name="top"></a>'
				'<div class="show_menu" style="display: none;">'
					'<a href="#" id="show_menu" title="Show menu" style="margin-top: 30px;position: absolute;">'
						'<span class="ui-state-default ui-corner-all">'
							'<span class="ui-icon ui-icon-arrowthick-1-e" id="arrow"></span>'
						'</span>'
					'</a>'
				'</div>'
				'<div class="top-menu">'
					'<div class="LogoText">'
						'<span style="padding: 10px;">HAproxy-WI</span>'
						'<a href="#" id="hide_menu" title="Hide menu" style="margin-left: 23px; position: absolute;">'
							'<span class="ui-state-default ui-corner-all">'
								'<span class="ui-icon ui-icon-arrowthick-1-w" id="arrow"></span>'
							'</span>'
						'</a>'
					'</div>')
	links()
	print('</div><div class="container">')
	
def links():
	print('<div class="top-link">'
		'<nav class="menu">'
			'<ul>'
				'<li><a title="Statistics, monitoring and logs" class="stats">Stats</a>'				
						'<li><a href=/cgi-bin/overview.py title="Server and service status" class="overview-link head-submenu">Overview</a> </li>'
						'<li><a href=/cgi-bin/viewsttats.py title"Show stats" class="stats head-submenu">Stats</a> </li>'
						'<li><a href=/cgi-bin/logs.py title="View logs" class="logs head-submenu">Logs</a></li>'
						'<li><a href=/cgi-bin/map.py title="View map" class="map head-submenu">Map</a></li>'				
				'</li>'
				'<li><a href=/cgi-bin/edit.py title="Runtime API" class="runtime">Runtime API</a> </li>'
				'<li><a title="Actions with configs" class="config-show">Configs</a>'					
						'<li><a href=/cgi-bin/configshow.py title="Show Config" class="config-show head-submenu">Show</a></li> '
						'<li><a href=/cgi-bin/diff.py title="Compare Configs" class="compare head-submenu">Compare</a></li>')
	if is_admin(level = 2):
		print('<li><a href=/cgi-bin/add.py#listner title="Add single listen" class="add head-submenu">Add listen</a></li>'
						'<li><a href=/cgi-bin/add.py#frontend title="Add single frontend" class="add head-submenu">Add frontend</a></li>'
						'<li><a href=/cgi-bin/add.py#backend title="Add single backend" class="add head-submenu">Add backend</a></li>'
						'<li><a href=/cgi-bin/config.py title="Edit Config" class="edit head-submenu">Edit</a> </li>')
	print('</li>')
	if is_admin(level = 2):
		print('<li><a title="Actions with configs" class="version">Versions</a>'			
				'<li><a href=/cgi-bin/configver.py title="Upload old versions configs" class="upload head-submenu">Upload</a></li>')
	if is_admin():
		print('<li><a href=/cgi-bin/delver.py title="Delete old versions configs" class="delete head-submenu">Delete</a></li>')
	if is_admin(level = 2):
		print('</li>')
	show_login_links()
	if is_admin():
		print('<li><a title="Admin area" class="version">Admin area</a>'			
					'<li><a href=/cgi-bin/users.py#users title="Actions with users" class="users head-submenu">Users</a></li>'
					'<li><a href=/cgi-bin/users.py#groups title="Actions with groups" class="group head-submenu">Groups</a></li>'
					'<li><a href=/cgi-bin/users.py#servers title="Actions with servers" class="runtime head-submenu">Servers</a></li>'
					'<li><a href=/cgi-bin/users.py#roles title="Users roles" class="role head-submenu">Roles</a></li>'
					'<li><a href=/cgi-bin/settings.py title="View settings" class="settings head-submenu">View settings</a></li>'
					'<li><a href=/cgi-bin/viewlogs.py title="View users actions logs" class="logs head-submenu">View logs</a></li>'
				'</li>')
	print('</ul>'
		  '</nav>'
		  '<div class="copyright-menu">HAproxy-WI v2.0.5</div>'
		  '</div>')	

def show_login_links():
	cookie = http.cookies.SimpleCookie(os.environ.get("HTTP_COOKIE"))
	login = cookie.get('login')
	
	if login is None:
		print('<li><a href=/cgi-bin/login.py? title="Login" class="login">Login</a></li>')	
	else:
		print('<li><a href=/cgi-bin/login.py?logout=logout title="Logout, user name: %s" class="login">Logout</a></li>' % login.value)
		  
def footer():
	print('</center></div>'
			'<center style="margin-left: 8%;">'
				'<h3>'
					'<a class="ui-button ui-widget ui-corner-all" href="#top" title="Move up">UP</a>'
				'</h3><br />'
			'</center>'
		'</body></html>')
def get_auto_refresh(h2):
	print('<h2>')
	print('<span>%s</span>' % h2)
	print('<span class="auto-refresh">'
			'<a id="0"><img style="margin-top: 3px; margin-left: -23px; position: fixed;" src=/image/pic/update.png alt="restart" class="icon"> Auto-refresh</a>'
			'<a id="1" style="display: none;"><img style="margin-top: 3px; margin-left: -23px; position: fixed;" src=/image/pic/update.png alt="restart" class="icon"> Auto-refresh</a>'
			'<a onclick="pauseAutoRefresh()" class="auto-refresh-pause" style="display: none; margin-top: 4px;"></a>'
			'<a onclick="pauseAutoResume()" class="auto-refresh-resume" style="display: none; margin-top: 4px;"></a>'
		'</span></h2>'
		'<div class="auto-refresh-div">'
			'<div class="auto-refresh-head">'
				'Refresh Interval'
			'</div>'
			'<div class="auto-refresh-interval">'
				'<div class="auto-refresh-ul">'
					'<ul>'
						'<li>'
							'<a class="ui-button ui-widget ui-corner-all" onclick="setRefreshInterval(0)" title="Turn off auto-refresh">Off</a> '
						'</li>'
					'</ul>'
				'</div>'
				'<div class="auto-refresh-ul">'
					'<ul>'
						'<li>'
							'<a title="Auto-refresh every 5 seconds" onclick="setRefreshInterval(5000)">5 seconds</a>'
						'</li>'
						'<li>'
							'<a title="Auto-refresh every 10 seconds" onclick="setRefreshInterval(10000)">10 seconds</a>'
						'</li>'
						'<li>'
							'<a title="Auto-refresh every 30 seconds" onclick="setRefreshInterval(30000)">30 seconds</a>'
						'</li>'
						'<li>'
							'<a title="Auto-refresh ever 45 seconds" onclick="setRefreshInterval(45000)">45 seconds</a>'		
						'</li>'
					'</ul>'
				'</div>'
				'<div class="auto-refresh-ul">'
					'<ul>'
						'<li>'
							'<a title="Auto-refresh every 1 minute" onclick="setRefreshInterval(60000)">1 minute</a>'
						'</li>'
						'<li>'
							'<a title="Auto-refresh every 5 minutes" onclick="setRefreshInterval(300000)">5 minutes</a>'
						'</li>'
						'<li>'
							'<a title="Auto-refresh every 15 minutes" onclick="setRefreshInterval(900000)">15 minutes</a>'
						'</li>'
						'<li>'
							'<a title="Auto-refresh ever 30 minutes" onclick="setRefreshInterval(1800000)">30 minutes</a>'		
						'</li>'
					'</ul>'
				'</div>'
				'<div class="auto-refresh-ul">'
					'<ul>'
						'<li>'
							'<a title="Auto-refresh every 1 hour" onclick="setRefreshInterval(3600000)">1 hour</a>'
						'</li>'
						'<li>'
							'<a title="Auto-refresh every 2 hour" onclick="setRefreshInterval(7200000)">2 hour</a>'
						'</li>'
						'<li>'
							'<a title="Auto-refresh every 12 hour" onclick="setRefreshInterval(43200000)">12 hour</a>'
						'</li>'
						'<li>'
							'<a title="Auto-refresh ever 1 day" onclick="setRefreshInterval(86400000)">1 day</a>'		
						'</li>'
					'</ul>'
				'</div>'
			'</div>'
		'</div>')
def ssh_connect(serv):
	ssh = SSHClient()
	ssh.load_system_host_keys()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		if config.get('ssh', 'ssh_keys_enable') == "1":
			k = paramiko.RSAKey.from_private_key_file(ssh_keys)
			ssh.connect(hostname = serv, username = ssh_user_name, pkey = k )
		else:
			ssh.connect(hostname = serv, username = ssh_user_name, password = config.get('ssh', 'ssh_pass'))
		return ssh
	except paramiko.AuthenticationException:
		print("Authentication failed, please verify your credentials: %s")
	except paramiko.SSHException as sshException:
		print("Unable to establish SSH connection: %s" % sshException)
	except paramiko.BadHostKeyException as badHostKeyException:
		print("Unable to verify server's host key: %s" % badHostKeyException)
	except Exception as e:
		print(e.args)	

def get_config(serv, cfg):
	os.chdir(hap_configs_dir)
	ssh = ssh_connect(serv)
	try:
		sftp = ssh.open_sftp()
		sftp.get(haproxy_config_path, cfg)
		sftp.close()
		ssh.close()
	except Exception as e:
		print("!!! There was an issue, " + str(e))
	
def show_config(cfg):
	print('<div style="margin-left: 16%" class="configShow">')
	conf = open(cfg, "r")
	i = 0
	for line in conf:
		i = i + 1
		if not line.find("global"):
			print('<span class="param">' + line + '</span><div>')
			continue
		if not line.find("defaults"):
			print('</div><span class="param">' + line + '</span><div>')
			continue
		if not line.find("listen"):
			print('</div><span class="param">' + line + '</span><div>')
			continue
		if not line.find("frontend"):
			print('</div><span class="param">' + line + '</span><div>')
			continue
		if not line.find("backend"):
			print('</div><span class="param">' + line + '</span><div>')
			continue
		if "acl" in line or "option" in line or "server" in line:
			if "timeout" not in line and "default-server" not in line and "#use_backend" not in line:
				print('<span class="paramInSec"><span class="numRow">')
				print(i)
				print('</span>' + line + '</span><br />')
				continue
		if "#" in line:
			print('<span class="comment"><span class="numRow">')
			print(i)
			print(line + '</span></span><br />')
			continue	
		if line.__len__() < 1:
			print('</div>')
		if line.__len__() > 1:
			print('<span class="configLine"><span class="numRow">')
			print(i)
			print('</span>' + line + '</span><br />')					
	print('</div></div>')
	conf.close
	
def upload_and_restart(serv, cfg, **kwargs):
	tmp_file = tmp_config_path + "/" + get_data('config') + ".cfg"

	ssh = ssh_connect(serv)
	print("<center>connected<br />")
	sftp = ssh.open_sftp()
	sftp.put(cfg, tmp_file)
	sftp.close()
	
	if kwargs.get("just_save") == "save":
		commands = [ "/sbin/haproxy  -q -c -f " + tmp_file, "mv -f " + tmp_file + " " + haproxy_config_path ]
	else:
		commands = [ "/sbin/haproxy  -q -c -f " + tmp_file, "mv -f " + tmp_file + " " + haproxy_config_path, restart_command ]
	
	i = 0
	for command in commands:
		i = i + 1
		print("</br>Executing: {}".format( command ))
		print("</br>")
		stdin , stdout, stderr = ssh.exec_command(command)
		print(stdout.read().decode(encoding='UTF-8'))
		if i == 1:
			if not stderr.read():
				print('<h3 style="color: #23527c">Config ok</h3>')
			else:
				print('<h3 style="color: red">In your config have errors, please check, and try again</h3>')
				print(stderr.read().decode(encoding='UTF-8'))
				return False
				break
		if i is not 1:
			print("</br>Errors:")	
			print(stderr.read().decode(encoding='UTF-8'))
			print("</br>")
	
	return True	
	
	print('</center>')
	ssh.close()

def check_haproxy_config(serv):
	commands = [ "/sbin/haproxy  -q -c -f %s" % haproxy_config_path ]
	ssh = ssh_connect(serv)
	for command in commands:
		stdin , stdout, stderr = ssh.exec_command(command)
		if not stderr.read():
			return True
		else:
			return False
			
def compare(stdout):
	i = 0
	minus = 0
	plus = 0
	total_change = 0
	
	print('</center><div class="out">')
	print('<div class="diff">')
		
	for line in stdout:
		i = i + 1

		if i is 1:
			print('<div class="diffHead">' + line + '<br />')
		elif i is 2:
			print(line + '</div>')
		elif line.find("-") == 0 and i is not 1:
			print('<div class="lineDiffMinus">' + line + '</div>')
			minus = minus + 1
		elif line.find("+") == 0 and i is not 2:
			print('<div class="lineDiffPlus">' + line + '</div>')	
			plus = plus + 1					
		elif line.find("@") == 0:
			print('<div class="lineDog">' + line + '</div>')
		else:
			print('<div class="lineDiff">' + line + '</div>')				
			
		total_change = minus + plus
	print('<div class="diffHead">Total change: %s, additions: %s & deletions: %s </div>' % (total_change, minus, plus))	
	print('</div></div>')
		
def show_log(stdout):
	i = 0
	for line in stdout:
		i = i + 1
		if i % 2 == 0: 
			print('<div class="line3">' + line + '</div>')
		else:
			print('<div class="line">' + line + '</div>')
			
def show_ip(stdout):
	for line in stdout:
		print(line)
		
def server_status(stdout):
	proc_count = ""
	i = 0
	for line in stdout.read().decode(encoding='UTF-8'):
		i = i + 1
		if i == 1:
			proc_count += line
			if line.find("0"):
				err = 1
			else:
				err = 0
			
	if err != 0:
		print('<span class="serverUp"> UP</span> running %s processes' % proc_count)
	else:
		print('<span class="serverDown"> DOWN</span> running %s processes' % proc_count)	
	
def ssh_command(serv, commands, **kwargs):
	ssh = ssh_connect(serv)
		  
	for command in commands:
		try:
			stdin, stdout, stderr = ssh.exec_command(command)
		except:
			continue
				
		if kwargs.get("ip") == "1":
			show_ip(stdout)
		elif kwargs.get("compare") == "1":
			compare(stdout)
		elif kwargs.get("show_log") == "1":
			show_log(stdout)
		elif kwargs.get("server_status") == "1":
			server_status(stdout)
		else:
			print('<div style="margin: -10px;">'+stdout.read().decode(encoding='UTF-8')+'</div>')
			
		print(stderr.read().decode(encoding='UTF-8'))

def choose_only_select(serv, **kwargs):
	if kwargs.get("virt"):
		listhap = sql.get_dick_permit(virt=1)
	else:
		listhap = sql.get_dick_permit()
		
	if kwargs.get("servNew"):
		servNew = kwargs.get("servNew")
	else:
		servNew = ""
	
	for i in listhap:
		if i[2] == serv or i[2] == servNew:
			selected = 'selected'
		else:
			selected = ''

		print('<option value="%s" %s>%s</option>' % (i[2], selected, i[1]))	

def chooseServer(formName, title, note, **kwargs):
	servNew = form.getvalue('serNew')
	
	print('<h2>' + title + '</h2><center>')
	print('<h3>Choose server</h3>')
	print('<form action=' + formName + ' method="get">')
	print('<p><select autofocus required name="serv" id="serv">')
	print('<option disabled>Choose server</option>')

	choose_only_select(serv, servNew=servNew)

	print('</select>')
	
	if kwargs.get("onclick") is not None:
		print('<a class="ui-button ui-widget ui-corner-all" id="show" title="Show config" onclick="%s">Show</a>' % kwargs.get("onclick"))
	else:
		get_button("Open", value="open")
		
	print('</p></form>')
	
	if note == "y":
		print('<p><b>Note:</b> If you reconfigure First server, second will reconfigured automatically</p>')
	print('</center>')

