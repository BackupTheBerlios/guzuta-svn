import os, sys, ftplib, tarfile, os.path, md5
import time, httplib, decimal, gzip, shutil

# Globals

root_dir = "/var/lib/pacman/"
cache_dir = "/var/cache/pacman/pkg/"

# This function is meant to run on startup.

def read_conf():
  """Reads /etc/pacman.conf and parses the Includes.
  Returns:
    1. a list of the whole file, line by line.
    2. a list of the servers, eg ["[current]", "[extra]"]
    3. a list of NoUpgrade
    4. a list of IgnorePkg"""
    
  file = open("/etc/pacman.conf", "r")
  file_string = file.read()
  file.close()
  conf_list = file_string.splitlines()
  server_list = []
  x = 0
  conf_list_1 = []
  
  for i in conf_list:
    x = x + 1
    if i.startswith("Include"):
      include_list = i.rsplit("=")
      file = open(include_list[-1].strip(), "r")
      file_string = file.read()
      file.close()
      include_list = file_string.splitlines()
      
      for i in include_list:
        conf_list.insert(x, i)
        x = x + 1
	
  for i in conf_list:
    i = i.strip()
    if i.startswith("["):
      if not i.startswith("[options]") and i not in server_list:
        server_list.append(i)
  
  conf_list_1 = conf_list[conf_list.index("[options]") + 1:]
  noupgrade_list = []
  ignore_list = []

  for i in conf_list_1:
    if i.startswith("["):
      pass
    elif i.startswith("NoUpgrade"):
      list = i.split("=")
      list = list[-1].strip().split()

      for i in list:
	      noupgrade_list.append(i)

    elif i.startswith("IgnorePkg"):
      list = i.split("=")
      list = list[-1].strip().split()

      for i in list:
	      ignore_list.append(i)
 
  return conf_list, server_list,  noupgrade_list, ignore_list


# Sync function

def sync(conf_list, server):
  """Syncronise the servers
  Vars:
    1. list 1(conf_list) from read_conf function
    2. the server, eg "[current]"
  Returns:
    1. host on success, "0" if the repo haven't been updated and None on failure"""
    
  index = conf_list.index(server)
  conf_list_new = conf_list[index + 1:]
  name = server.lstrip("[")
  name = name.rstrip("]")
  dir = root_dir + name + "/"
  
  try:
    file = open(dir + ".lastupdate", "r")
    timestamp_old = file.read().split()[-1]
    file.close()
  except:
    timestamp_old = None
    
  for s in conf_list_new:
    #print 'hello'
    #print 's: <%s>' % s
    #print 'bye'
    if s.startswith("["):
      #print 'A'
      if s != server:
        return None
      
    if s.startswith("Server"):
      #print 'B'
      s_list = s.rsplit("=")
      prot = s_list[-1].strip()
      s_list = prot.rsplit("//")
      str = s_list[-1]
      s_list = str.rsplit("/")
      host = s_list[0]
      
      s_list = s_list[1:]
      cwd = ""
	
      for i in range(len(s_list)):
	      cwd = "/" + s_list.pop() + cwd
      
      if prot.startswith("ftp"):
        try:
          ftp_class = ftplib.FTP(host)
          ftp_class.login("anonymous")
          ftp_class.cwd(cwd)
          cmd = "MDTM " + name + ".db.tar.gz"
          timestamp = ftp_class.sendcmd(cmd).split()[-1]
	        
          if timestamp_old == timestamp:
            return "0"
          
          if os.path.isdir(dir):
            dir_list = os.listdir(dir)
      
            for i in dir_list:
              if os.path.isdir(dir + i):
                dir_list_1 = os.listdir(dir + i)

                for f in dir_list_1:
                  os.remove(dir + i + "/" + f)
	  
                os.rmdir(dir + i)
              else:
                os.remove(dir+ i)
	
          else:
            os.mkdir(dir, 0755)
	    
          file = open(dir + ".lastupdate", "w")
          file.write(timestamp)
          file.close()
          cmd = "RETR " + name + ".db.tar.gz"
          loc_file = open(cache_dir + name + ".db.tar.gz", 'wb')
          out = ftp_class.retrbinary(cmd, loc_file.write)
          loc_file.close()
          ftp_class.close()
          tar = tarfile.open(cache_dir + name + ".db.tar.gz", "r:gz")

          for i in tar:
            tar.extract(i, dir)

          os.remove(cache_dir + name + ".db.tar.gz")
      	  return host
          
        except:
          pass

      elif prot.startswith("http"):
        try:
          http_class = httplib.HTTPConnection(host)
          http_class.request("GET", cwd + "/" + name + ".db.tar.gz")
          req = http_class.getresponse()
          out = req.read()
          http_class.close()
          loc_file = open(cache_dir + name + ".db.tar.gz", 'wb')
          loc_file.write(out)
          loc_file.close()
          	  
          if os.path.isdir(dir):
            dir_list = os.listdir(dir)
      
            for i in dir_list:
              if os.path.isdir(dir + i):
                dir_list_1 = os.listdir(dir + i)

                for f in dir_list_1:
                  os.remove(dir + i + "/" + f)
	  
                os.rmdir(dir + i)
              else:
                os.remove(dir+ i)
	
          else:
            os.mkdir(dir, 0755)
	    
          tar = tarfile.open(cache_dir + name + ".db.tar.gz", "r:gz")
          for i in tar:
            tar.extract(i, dir)
        
          os.remove(cache_dir + name + ".db.tar.gz")
          return host
  
        except:
          pass

  return None
  

# Exist_check

def exist_check(name, server_list):
  """Checking if package exist on the server.
  Vars:
    1. name of package
    2. list 2 from read_conf function
  Returns:
    1. None if var 1 is "", "0" if package didn't exist and "1" if it did.
    2. the repo, eg "current"
    3. the package
    4. the package name
    5. "1" if package exist in cache or None if it's not"""
    
  if name == "":
    return None, None, None, None, None
  
  retcode = "0"
  cache = None

  for server in server_list:
    repo = server.lstrip("[")
    repo = repo.rstrip("]")
    dir_list = os.listdir(root_dir + repo)
    dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))

    for package in dir_list:
      if package.startswith(name):
        pack_name, ver, rel = get_name(package)

        if pack_name == name:
          retcode = "1"
          break

    if retcode == "1":
      break

  if os.path.exists(cache_dir + package + ".pkg.tar.gz"):
    cache = "1"

  return retcode, repo, package, name, cache


# Provide check

def provide_check(name, server_list):
  """"""
  package, pack_name = provide_check_local(name)

  if package != None:
    return "1", package, pack_name
	  
  for server in server_list:
    repo = server.lstrip("[")
    repo = repo.rstrip("]")
    dir_list = os.listdir(root_dir + repo)
    dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
    
    for package in dir_list:
      try:
        file = open(root_dir + repo + "/" + package + "/depends", "r")
        file_str = file.read()
        file.close()
        file_list = file_str.splitlines()
        file_list = file_list[file_list.index("%PROVIDES%") + 1:]
	  
        for i in file_list:
          if i.startswith("%"):
	    break
          else:
            if i == name:
              pack_name, ver, rel = get_name(package)
              return "2", package, pack_name
      except:
        pass

  return None, None, None


def provide_check_local(name):
  """"""
  dir_list = os.listdir(root_dir + "local")
  dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
  
  for package in dir_list:
    try:
      file = open(root_dir + "local/" + package + "/depends", "r")
      file_str = file.read()
      file.close()
      file_list = file_str.splitlines()
      file_list = file_list[file_list.index("%PROVIDES%") + 1:]
      
      for i in file_list:
        if i.startswith("%"):
	  break
        else:
          if i == name:
	    pack_name, ver, rel = get_name(package)
	    return package, pack_name
    except:
      pass

  return None, None


# Control function for dependency checking

def dep_single(name, server_list):
  if name == "":
    return None, None, None, None, None 

  package_list, dep_list, err_list, conflict_list, size = dep_install([name], server_list)

  return package_list, dep_list, err_list, conflict_list, size


def dep_install(check_list, server_list):
  if check_list == [] or check_list == [""]:
    return None, None, None, None, None

  err_list = []
  package_list = []
  dep_list = []
  conflict_list = []

  while check_list != []:
    dep_list_check = []
    x = len(check_list)

    for i in check_list:
      if i in dep_list:
        pass
      else:
        retcode, repo, package, name, cache = exist_check(i, server_list)
        if retcode == None:
          retcode, package, pack_name = provide_check(i, server_list)
          if retcode == "2":
            check_list.append(pack_name)
          elif retcode == None:
            err_list.append(i)

        elif retcode == "1":
          dep_list.insert(0, i)
          package_list.append(package)
          check_list_1 = dep_check(package, repo)
          check_list = check_list + check_list_1

    check_list = check_list[x:]
    
  size = 0
  if err_list == []:
    for package in package_list:
      mode = "0"
      for server in server_list:
        repo = server.lstrip("[")
        repo = repo.rstrip("]")
        dir_list = os.listdir(root_dir + repo)
        dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
	
        for dir in dir_list:
          if dir == package:
            mode = "1"
            file = open(root_dir + repo + "/" + dir + "/depends", "r")
            file_str = file.read()
            file.close()
            file_list = file_str.splitlines()
      
            try:
              file_list = file_list[file_list.index("%CONFLICTS%") + 1:file_list.index("%PROVIDES%") - 1]
              local_list = os.listdir(root_dir + "local")
              local_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
      
              if file_list != []:
                for name in file_list:
                  if name != "":
                    for p in local_list:
                      if p.startswith(name):
                        pack_name, ver, rel = get_name(p)

                        if pack_name == name:
                          conflict_list.append(name)
                          break
	    
            except:
	            pass
	    
            file = open(root_dir + repo + "/" + package + "/desc", "r")
            file_str = file.read()
            file.close()
            file_list = file_str.splitlines()
            try:
              size = int(file_list[file_list.index("%CSIZE%") + 1]) + size
              break
            except:
              break
	      
        if mode == "1":
	        break
  
  return package_list, dep_list, err_list, conflict_list, size


# Dep check

def dep_check(package, repo):
  dep_list = []
  file = open(root_dir + repo + "/" + package + "/depends", "r")
  file_str = file.read()
  file.close()
  file_list = file_str.splitlines()
  try:
    file_list = file_list[file_list.index("%DEPENDS%") + 1:]
  except:
    return dep_list

  for name in file_list:
    if name.startswith("%"):
      break
    elif name == "":
      pass
    else:
      dep_list.append(name)
 
  dep_list_1 = []
  dep_list_2 = []
  
  for i in dep_list:
    if "=" in i and ">" in i:
      name = i.split(">")[0]
      ver = i.split("=")[-1]
      pack_loc, ver_loc, rel = get_local_package(name)
      if pack_loc == None:
        dep_list_1.append(name)
        dep_list_2.append(i)
      else:
        package = name + "-" + ver + "-1"
        retcode = version_compare(pack_loc, package)
        if retcode == "1":
          dep_list_1.append(name)
          dep_list_2.append(i)
        else:
          dep_list_2.append(i)

    else:
      package, ver, rel = get_local_package(i)
      if package != None:
        dep_list_2.append(i)

  for i in dep_list_1:
    dep_list.append(i)
  
  for i in dep_list_2:
    dep_list.remove(i)
    
  return dep_list


# Download function

def download(conf_list, repo, package):
  conf_list_new = conf_list[conf_list.index("[" + repo + "]") + 1:]
  
  for s in conf_list_new:
    if s.startswith("["):
      if s != "[" + repo + "]":
        break
    if s.startswith("Server"):
      s_list = s.rsplit("=")
      server = s_list[-1].strip()
      s_list = server.rsplit("//")
      str = s_list[-1]
      s_list = str.rsplit("/")
      host = s_list[0]

      s_list = s_list[1:]
      cwd = ""

      for i in range(len(s_list)):
        cwd = "/" + s_list.pop() + cwd

      if server.startswith("ftp"):
        try:
          ftp_class = ftplib.FTP(host)
          ftp_class.login("anonymous")
          ftp_class.cwd(cwd)
          cmd = "RETR " + package + ".pkg.tar.gz"
          loc_file = open(cache_dir + package + ".pkg.tar.gz", 'wb')
          out = ftp_class.retrbinary(cmd, loc_file.write)
          ftp_class.close()
          loc_file.close()
          return "1"

        except:
            if os.path.exists(cache_dir + package + ".pkg.tar.gz"):
              loc_file.close()
            os.remove(cache_dir + package + ".pkg.tar.gz")
        
	
      elif server.startswith("http"):
        try:
          http_class = httplib.HTTPConnection(host)
          http_class.request("GET", cwd + "/" + package + ".pkg.tar.gz")
          req = http_class.getresponse()
          out = req.read()
          http_class.close()
          loc_file = open(cache_dir + package + ".pkg.tar.gz", 'wb')
          loc_file.write(out)
          loc_file.close()
          return "1"
        
        except:
          pass

  return None


# MD5SUM check function

def md5sum_check(repo, package):
  retcode = "0"
  desc_file = open(root_dir + repo + "/" + package + "/desc", "r")
  desc = desc_file.read()
  desc_file.close()
  desc_list = desc.splitlines()
  md5sum = desc_list[desc_list.index("%MD5SUM%") + 1]
  package_file = open(cache_dir + package + ".pkg.tar.gz", "rb")
  package_string = package_file.read()
  md5_obj = md5.new(package_string)
  package_file.close()
  md5_obj_sum = md5_obj.hexdigest()
  
  if md5sum == md5_obj_sum:
    retcode = "1"
    
  return retcode


# Check if package already exists in system

def old_check(name):
  package, ver, rel = get_local_package(name)

  if package != None:
    file = open(root_dir + "local/" + package +"/depends", "r")
    file_str = file.read()
    file.close()
    depends_list = file_str.splitlines()
    file = open(root_dir + "local/" + package +"/desc", "r")
    file_str = file.read()
    file.close()
    desc_list = file_str.splitlines()
    try:
      reason = desc_list[desc_list.index("%REASON%") + 1]
    except:
      reason = "0"
    return package, depends_list, reason,  ver

  return None, None, None, None


# Get local package from name

def get_local_package(name):
  dir_list = os.listdir(root_dir + "local")
  dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))

  for package in dir_list:
    if package.startswith(name):
      pack_name, ver, rel = get_name(package)

      if pack_name == name:
	return package, ver, rel

  return None, None, None


# Install

def install(package, name, depends_list, noupgrade_list, reason, oldver, pack_path):
  pkgver = package.split("-")[-2]
  path = root_dir + "local/" + package + "/"
  os.mkdir(path)
  
  if pack_path == None:
    tar = tarfile.open(cache_dir + package + ".pkg.tar.gz", "r:gz")
  else:
    tar = tarfile.open(pack_path + "/" + package + ".pkg.tar.gz", "r:gz")
  
  files_list = tar.getnames()
  files_list.insert(0, "%FILES%")
  files_list.append("\n%BACKUP%\n")
  
  files_str = ""
  for i in files_list:
    if i != ".FILELIST" and i != ".PKGINFO" and i != ".INSTALL":
      files_str = files_str + i + "\n"
  
  file = open(path + "files", "w")
  file.write(files_str)
  file.close()
  
  for i in tar:
    file_path = i.name
    if file_path not in noupgrade_list:
      tar.extract(i, "/")
    else:
      file = tar.extractfile(i)
      out = file.read()
      file = open("/" + file_path + ".pacnew", "w")
      file.write(out)
      file.close()
  
  tar.close()  
  
  try:
    os.remove("/.FILELIST")
  except:
    pass
    
  try:
    file = file = open("/.INSTALL", "r")
    install_str = file.read().strip()
    file.close()
    file = open(path + "install", "w")
    file.write(install_str)
    file.close()
    os.remove("/.INSTALL")
  except:
    pass
  
  file = open("/.PKGINFO", "r")
  pkginfo_str = file.read()
  file.close()
  os.remove("/.PKGINFO")
  pkginfo_list = pkginfo_str.splitlines()
  
  desc_list_new = ["%NAME%", "\n",  "\n", "%VERSION%", "\n", "\n", "%DESC%", "\n", "\n", "%GROUPS%",\
	        "\n", "\n", "%URL%", "\n", "\n", "%LICENSE%", "\n", "\n", "%ARCH%","\n", "\n",\
		"%BUILDDATE%","\n", "\n", "%INSTALLDATE%", "\n", "\n", "%PACKAGER%", "\n", "\n",\
		"%SIZE%","\n", "\n", "%REASON%", "\n"]

  depends_list_new = ["%DEPENDS%", "\n", "\n", "%REQUIREDBY%", "\n", "\n", "%CONFLICTS%",\
		      "\n", "\n", "%PROVIDES%", "\n"]
  
  
  desc_list_new.insert(desc_list_new.index("%REASON%") + 2, reason + "\n")
  time_str = time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime())
  desc_list_new.insert(desc_list_new.index("%INSTALLDATE%") + 2, time_str + "\n")
  dep_list = []
  
  for i in pkginfo_list:
    if i.startswith("pkgname"):
      list = i.split("=") 
      data = list[-1].strip()
      desc_list_new.insert(desc_list_new.index("%NAME%") + 2, data + "\n")
    elif i.startswith("pkgver"):
      list = i.split("=") 
      data = list[-1].strip()
      desc_list_new.insert(desc_list_new.index("%VERSION%") + 2, data + "\n")
    elif i.startswith("pkgdesc"):
      list = i.split("=") 
      data = list[-1].strip()
      desc_list_new.insert(desc_list_new.index("%DESC%") + 2, data + "\n")
    elif i.startswith("group"):
      list = i.split("=") 
      data = list[-1].strip()
      desc_list_new.insert(desc_list_new.index("%GROUPS%") + 2, data + "\n")
    elif i.startswith("url"):
      list = i.split("=") 
      data = list[-1].strip()
      desc_list_new.insert(desc_list_new.index("%URL%") + 2, data + "\n")
    elif i.startswith("license"):
      list = i.split("=") 
      data = list[-1].strip()
      desc_list_new.insert(desc_list_new.index("%LICENSE%") + 2, data + "\n")
    elif i.startswith("arch"):
      list = i.split("=") 
      data = list[-1].strip()
      desc_list_new.insert(desc_list_new.index("%ARCH%") + 2, data + "\n")
    elif i.startswith("builddate"):
      list = i.split("=") 
      data = list[-1].strip()
      desc_list_new.insert(desc_list_new.index("%BUILDDATE%") + 2, data + "\n")
    elif i.startswith("packager"):
      list = i.split("=") 
      data = list[-1].strip()
      desc_list_new.insert(desc_list_new.index("%PACKAGER%") + 2, data + "\n")
    elif i.startswith("size"):
      list = i.split("=") 
      data = list[-1].strip()
      desc_list_new.insert(desc_list_new.index("%SIZE%") + 2, data + "\n")
    elif i.startswith("conflict"):
      list = i.split("=") 
      data = list[-1].strip()
      depends_list_new.insert(depends_list_new.index("%CONFLICTS%") + 2, data + "\n")
    elif i.startswith("provide"):
      list = i.split("=") 
      data = list[-1].strip()
      depends_list_new.insert(depends_list_new.index("%PROVIDES%") + 2, data + "\n")
    elif i.startswith("depend"):
      list = i.split("=", 1)
      data = list[-1].strip()
      depends_list_new.insert(depends_list_new.index("%DEPENDS%") + 2, data + "\n")
      dep_list.append(data)
      
  desc_str = ""
  for i in desc_list_new:
    desc_str = desc_str + i
  
  file = open(path + "desc", "w")
  file.write(desc_str)
  file.close()
   
  if depends_list != None:
    try:
      depends_list = depends_list[depends_list.index("%REQUIREDBY%") + 1:depends_list.index("%CONFLICTS%") - 1]
      depends_list.sort(lambda y,x : cmp (x.lower(), y.lower()))
      depends_list.append("")
      for i in depends_list:
        if i.startswith("%"):
          break
        elif i == "":
          pass
        else:
          depends_list_new.insert(depends_list_new.index("%REQUIREDBY%") + 2, i + "\n")
    except:
      pass
      
  depends_str = ""
  for i in depends_list_new:
    depends_str = depends_str + i
  
  file = open(path + "depends", "w")
  file.write(depends_str)
  file.close()
	    
  package_list = []
  
  for i in dep_list:
    if ">" in i:
      i = i.split(">")[0]
    
    package, ver, rel = get_local_package(i)
    if package != None:
      package_list.append(package)
    
    else:
      package, pack_name = provide_check_local(i)
      if package != None:
        package_list.append(package)
      
  for p in package_list:
    file = open(root_dir + "local/" + p + "/depends", "r")
    file_str = file.read()
    file.close()
    depend_list = file_str.splitlines()
    depend_list.insert(depend_list.index("%REQUIREDBY%") + 1, name)
    depend_list_1 = depend_list[:depend_list.index("%REQUIREDBY%") + 1]
    depend_list_2 = depend_list[depend_list.index("%REQUIREDBY%") + 1:depend_list.index("%CONFLICTS%") - 1]
    depend_list_3 = depend_list[depend_list.index("%CONFLICTS%"):]
    depend_list_2.sort(lambda x,y : cmp (x.lower(), y.lower()))
    depend_list_2.append("")

    depend_list = depend_list_1 + depend_list_2 + depend_list_3
    depend_string = ""
    for j in depend_list:
      depend_string = depend_string + j + "\n"

    file = open(root_dir + "local/" + p + "/depends", "w")
    file.write(depend_string)
    file.close()

  try:
    file = open(path + "install", "r")
    file.close()
    cwd = os.getcwd()
    os.chdir("/")
    if oldver == None:
      os.system("echo " + '"' + "umask 0022;" + "source " + path + "install" + " post_install " + pkgver + '"' + "|chroot /")
      os.chdir(cwd)
    else:
      os.system("echo " + '"' + "umask 0022;" + "source " + path + "install" + " post_upgrade " + pkgver + " " + oldver +\
		'"' + "|chroot /")
      os.chdir(cwd)
  except:
    pass

  os.popen("/sbin/ldconfig -r /")


# Require check function

def require_check(name):  
  dir_list = os.listdir(root_dir + "local")
  dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
  require_list = []
  
  for package in dir_list:
    if package.startswith(name):
      pack_name, ver, rel = get_name(package)

      if pack_name == name:
        file = open(root_dir + "local/" + package +"/depends", "r")
        file_str = file.read()
        file.close()
        file_list = file_str.splitlines()
	file_list = file_list[file_list.index("%REQUIREDBY%") + 1:]

	for i in file_list:
	  if i.startswith("%") or i == "":
	    break
          else:
	    require_list.append(i)
	return package, require_list

  return None, None


# Control function for removing dependencies

def dep_remove(name):
  if name == "":
    return None, None, None
    
  package, require_list = require_check(name)
  
  if package == None:
    return "0", None, None
    
  if require_list != []:
    return "1", None, require_list
  
  dep_list = [name]
  package_list = [package]
  file = open(root_dir + "local/" + package + "/depends", "r")
  file_str = file.read()
  file.close()
  file_list = file_str.splitlines()
  try:
    file_list = file_list[file_list.index("%DEPENDS%") + 1:]
  except:
    pass

  dep_list_check = []
  for name in file_list:
    if name.startswith("%") or name == "":
      break
    if ">" in name:
      name_list = name.split(">")
      name = name_list[0]
      mode = 1
      dep_list_check.append(name)
    elif "=" in name:
      name_list = name.split("=")
      name = name_list[0]
      mode = 1
      dep_list_check.append(name)
    else:
      dep_list_check.append(name)
 
  dep_list_1 = []
  
  while dep_list_check != []:
    for name in dep_list_check:
      package, require_list = require_check(name)
      for i in dep_list:
	      try:
	        require_list.remove(i)
	      except:
	        pass
      if require_list == []:
        file = open(root_dir + "local/" + package + "/desc", "r")
        file_str = file.read()
        file.close()
        desc_list = file_str.splitlines()
        reason = desc_list[desc_list.index("%REASON%") + 1]

        if reason == "1":
          if name not in dep_list:
            dep_list.append(name)
            package_list.append(package)
          file = open(root_dir + "local/" + package + "/depends", "r")
          file_str = file.read()
          file.close()
          depends_list = file_str.splitlines()
          try:
            depends_list = depends_list[depends_list.index("%DEPENDS%") + 1:]
            for i in depends_list:
              if i.startswith("%") or i == "":
                break
              if ">" in name:
                name_list = name.split(">")
                name = name_list[0]
                mode = 1
                dep_list_1.append(name)
              elif "=" in name:
                name_list = name.split("=")
                name = name_list[0]
                mode = 1
                dep_list_1.append(name)
              else:
		            dep_list_1.append(i)
          except:
            pass
    dep_list_check = dep_list_1
    dep_list_1 = []
  
  return dep_list, package_list, None


# Get name from package

def get_name(package):
  list = package.split("-")
  ver = list[-2]
  rel = list[-1]
  list = list[:-2]
  x = 1

  for i in range(len(list) - 1):
    list.insert(x, "-")
    x = x + 2

  name = ""
  for i in list:
    name = name + i

  return name, ver, rel


# Dependency checking when removing groups

def dep_remove_group(name):
  if name == "":
    return None, None

  dir_list = os.listdir(root_dir + "local")
  dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
  dep_list = []
  package_list = []
  for i in dir_list:
    try:
      file = open(root_dir + "local/" + i + "/desc", "r")
      file_str = file.read()
      file.close()
      file_list = file_str.splitlines()

      file_list = file_list[file_list.index("%GROUPS%") + 1:file_list.index("%URL%") - 1]
      for g in file_list:
        if g == name:
          package_list.append(i)
          pack_name, ver, rel = get_name(i)
          dep_list.append(pack_name)
    except:
      pass

  dep_list_1 = []
  package_list_1 = []
  dep_list_check = dep_list
  dep_list_2 = []

  while dep_list_check != []:
    for i in dep_list_check:
      old_package, depends_list, reason, oldver = old_check(i)
      if oldver == None:
        pass
      else:
        if i not in dep_list_1 and i not in dep_list:
          if reason == "1":
            dep_list.append(i)
        try:
          depends_list = depends_list[depends_list.index("%DEPENDS%") + 1:]
          for g in depends_list:
            if g.startswith("%") or g == "":
	            break
            if ">" in g:
              g = g.split(">")[0]
            elif "=" in name:
              g = g.split("=")[0]
            if g not in dep_list_1 and g not in dep_list:
              dep_list_2.append(g)
              
        except:
          pass

    dep_list_check = dep_list_2
    dep_list_2 = []

  dep_list_2 = None

  while dep_list_2 != []:
    dep_list_2 = []

    for i in dep_list:
      package, require_list = require_check(i)
      require_list_1 = []
      
      for g in require_list:
        if g in dep_list:
	        require_list_1.append(g)
	
      for g in require_list_1:
        require_list.remove(g)
    
      if require_list != []:
        dep_list_2.append(i)
	    
    for g in dep_list_2:
      dep_list.remove(g)

  package_list = []
  for i in dep_list:
    package, ver, rel = get_local_package(i)
    package_list.append(package)

  dep_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
  package_list.sort(lambda x,y : cmp (x.lower(), y.lower()))

  return dep_list, package_list


# Remove function

def remove(package, name, noupgrade_list):
  path = root_dir + "local/" + package + "/"
  pkgver = package.split("-")[-2]
  
  try:
    file = open(path + "install", "r")
    file.close()
    cwd = os.getcwd()
    os.chdir("/")
    os.system("echo " + '"' + "umask 0022; " + "source " + path + "install" + " pre_remove " + pkgver + '"' + "|chroot /")
    os.chdir(cwd)
  except:
    pass

  try:
    file = open(path + "files", "r")
    file_str = file.read()
    file.close()
    file_list = file_str.splitlines()
    file_list = file_list[file_list.index("%FILES%") + 1:]

    file_1 = open(path + "depends", "r")
    file_str_1 = file_1.read()
    file_1.close()
    depend_list = file_str_1.splitlines()
    depend_list = depend_list[depend_list.index("%DEPENDS%") + 1:depend_list.index("%REQUIREDBY%") - 1]
  except:
    shutil.rmtree(path)
    return

  
  for i in file_list:
    try:
      if i not in noupgrade_list:
        i = "/" + i
        if os.path.isfile(i):
          os.remove(i)
        else:
          if i.startswith("%"):
            break
    except:
      pass
  
  try:
    file = open(path + "install", "r")
    file.close()
    cwd = os.getcwd()
    os.chdir("/")
    os.system("echo " + '"' + "umask 0022; " + "source " + path + "install" + " post_remove " + pkgver + '"' + "|chroot /")
    os.chdir(cwd)
  except:
    pass

  shutil.rmtree(path)
  
  package_list = []
 
  for i in depend_list:
    if ">" in i:
      i = i.split(">")[0]
    
    package, ver, rel = get_local_package(i)
    if package != None:
      package_list.append(package)
    
    else:
      package, pack_name = provide_check_local(i)
      if package != None:
        package_list.append(package)
  
  
  for p in package_list:
    file = open(root_dir + "local/" + p + "/depends", "r")
    file_str = file.read()
    file.close()
    depend_list = file_str.splitlines()
    depend_list_1 = depend_list[:depend_list.index("%REQUIREDBY%") + 1]
    depend_list_2 = depend_list[depend_list.index("%REQUIREDBY%") + 1:]

    for g in depend_list_2:
      if g.startswith("%"):
        break
      if g == name:
        depend_list_2.remove(g)
        depend_list = depend_list_1 + depend_list_2
	break

    depend_string = ""

    for j in depend_list:
      depend_string = depend_string + j + "\n"

    file = open(root_dir + "local/" + p + "/depends", "w")
    file.write(depend_string)
    file.close()

  os.popen("/sbin/ldconfig -r /")


# Update

def check_update(server_list, ignore_list):
  dir_list = os.listdir(root_dir + "local")
  dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
  update_list = []
  
  for repo in server_list:
    repo = repo.lstrip("[")
    repo = repo.rstrip("]")
    repo_list = os.listdir(root_dir + repo)
    repo_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
    check_list = []
    for package in dir_list:
      name, ver, rel = get_name(package)

      if name not in ignore_list:
        for pac_new in repo_list:
          if pac_new.startswith(name):
            name_1, ver, rel = get_name(pac_new)
  
            if name_1 == name:
              check_list.append(package)
              retcode = version_compare(package, pac_new)
              if retcode == "0" or retcode == None:
                break

              elif retcode == "1":
                update_list.append(name)
                break

    for i in check_list:
      dir_list.remove(i)

  return update_list
  

# Check group

def dep_group_install(name, server_list):
  group_list = []
  size = 0
  package_list = None
  err_list = None
  conflict_list = None
  dep_list = []

  if name == "":
    return None, None, None, None, None, None

  for server in server_list:
    repo = server.lstrip("[")
    repo = repo.rstrip("]")
    dir_list = os.listdir(root_dir + repo)
    for package in dir_list:
      if os.path.isdir(root_dir + repo + "/" + package):
        file = open(root_dir + repo + "/" + package + "/desc", "r")
        file_str = file.read()
        file.close()
        file_list = file_str.splitlines()

        try:
          file_list = file_list[file_list.index("%GROUPS%") + 1:]
          for i in file_list:
            if i.startswith("%"):
	            break
            else:
              if i == name:
                pack_name, ver, rel = get_name(package)
              
	        if pack_name not in group_list:
	          group_list.append(pack_name)
        except:
          pass

  if group_list != []:
    package_list, dep_list, err_list, conflict_list, size = dep_install(group_list, server_list)
    package_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
    for i in group_list:
      dep_list.remove(i)

  return group_list, package_list, dep_list, err_list, conflict_list, size


# Search function

def search(name, server_list):
  package_list = []
  repo_list = []
  if name == "" or None:
    return None, None

  for i in server_list:
    i = i.lstrip("[")
    i = i.rstrip("]")
    file_list = os.listdir(root_dir + i)
    
    for file in file_list:
      out = file.rfind(name)
      if out != -1:
        package_list.append(file)
        repo_list.append(i)

  return package_list ,repo_list

# Desc search

def desc_search(search_list, server_list):
  package_list = []
  repo_list = []
  
  if search_list == [] or search_list == [""] or search_list == [" "]:
    return None, None

  for i in server_list:
    i = i.lstrip("[")
    i = i.rstrip("]")
    dir_list = os.listdir(root_dir + i)
    
    for p in dir_list:
      try:
        file = open(root_dir + i + "/" + p + "/desc", "r")
        file_str = file.read()
        file.close()
        file_list = file_str.splitlines()
        file_list = file_list[file_list.index("%DESC%") + 1:file_list.index("%CSIZE%") - 1]
      
        for g in file_list:
          x = 0
          for h in search_list:
            out = g.rfind(h)
            if out != -1:
              x = x + 1
	
          if x == len(search_list):
            package_list.append(p)
            repo_list.append(i)
      except:
	      pass
	
  return package_list ,repo_list


# Search group

def search_group(name, server_list):
  group_list = []
  for server in server_list:
    repo = server.lstrip("[")
    repo = repo.rstrip("]")
    dir_list = os.listdir(root_dir + repo)
	
    for dir in dir_list:
      try:
        file = open(root_dir + repo + "/" + dir + "/desc", "r")
        file_str = file.read()
        file.close()
        file_list = file_str.splitlines()

        file_list = file_list[file_list.index("%GROUPS%") + 1:]
        for i in file_list:
          if name in i:
            if not i in group_list:
              group_list.append(i)

      except:
	      pass
        
  group_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
  return group_list


# Version compare

def version_compare(pack_0, pack_1):
  pac_list_0 = pack_0.split("-")
  pac_list_0 = pac_list_0[-2:]
  pac_rel_0 = pac_list_0[-1]
  pac_list_0 = pac_list_0[0].split(".")
  pac_list_0.append(pac_rel_0)

  pac_list_1 = pack_1.split("-")
  pac_list_1 = pac_list_1[-2:]
  pac_rel_1 = pac_list_1[-1]
  pac_list_1 = pac_list_1[0].split(".")
  pac_list_1.append(pac_rel_1)

  for i in range(len(pac_list_1)):
    try:
      x = pac_list_0[i]
      y = pac_list_1[i]
      if len(x) < len(y):
        return "1"
      elif len(x) > len(y):
	      return "0"
      z = cmp(x, y)
      if z > 0:
        return "0"
	  
      elif z < 0:
        return "1"
    except:
      return "1"
    
  return None
	

# Clear cache function

def clear_cache():
  """Clears the packagecache completely."""
  shutil.rmtree(cache_dir)
  os.mkdir(cache_dir)

# Print cache

def print_cache():
  dir_list = os.listdir(cache_dir)
  dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
  
  return dir_list


# Remove old cache

def remove_old_cache():
  dir_list = os.listdir(cache_dir)
  dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))

  for i in dir_list:
    name_0, ver, rel = get_name(i)

    for h in dir_list:
      if h.startswith(name_0):
	if h == i:
	  pass
	else:
	  name_1, ver, rel = get_name(h)
	  if name_1 == name_0:
            retcode = version_compare(i, h)
	    if retcode == "1":
	      os.remove(cache_dir + i)


# Remove uninstalled cache

def remove_uninstalled_cache():
  dir_list = os.listdir(cache_dir)
  loc_list = os.listdir(root_dir + "local")
  loc_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
  
  for i in dir_list:
    mode = "0"
    name_0, ver, rel = get_name(i)

    for g in loc_list:
      if g.startswith(name_0):
	      name_1, ver, rel = get_name(g)
  
      if name_0 == name_1:
	      mode = "1"

      if mode == "0":
        os.remove(cache_dir + i)
	
	
# Orphans

def orphans():
  dir_list = os.listdir(root_dir + "local")
  dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
  orphan_list = []
  for i in dir_list:
    try:
      file = open(root_dir + "local/" + i + "/desc", "r")
      file_str = file.read()
      file.close()
      file_list = file_str.splitlines()
      reason = file_list[file_list.index("%REASON%") + 1]

      if reason == "1":
        file = open(root_dir + "local/" + i + "/depends", "r")
        file_str = file.read()
        file.close()
        file_list = file_str.splitlines()
        file_list = file_list[file_list.index("%REQUIREDBY%") + 1:file_list.index("%CONFLICTS%") - 1:]
	
        if file_list == [] or file_list == [""]:
	        orphan_list.append(i)

    except:
      pass

  return orphan_list
 

# List installed packages
def list_locals():
  dir_list = os.listdir(root_dir + "local")
  dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
  return dir_list

# Get installed package
def get_loc_pack(name):
  dir_list = os.listdir(root_dir + "local")
  dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
  for i in dir_list:
    if i.startswith(name):
      name_1, ver, rel = get_name(i)
      if name == name_1:
        return i
      else:
        return None
      

# Installed package information
def loc_pack_info(name):
  package = get_loc_pack(name)
  if package == None:
    return None
  
  package_path = root_dir + "local/" + package
  file_desc = open(package_path + "/desc", "r")
  package_desc = file_desc.read()
  file_desc.close()
  file_depends = open(package_path + "/depends", "r")
  package_depends = file_depends.read()
  file_depends.close()
  package_desc_list = package_desc.splitlines()
  package_depends_list = package_depends.splitlines()
  
  info_list = []
  index = package_desc_list.index("%NAME%")
  info = package_desc_list[index + 1]
  info_list.append(info)
  
  index = package_desc_list.index("%VERSION%")
  info = package_desc_list[index + 1]
  info_list.append(info)
  
  index = package_desc_list.index("%DESC%")
  info = package_desc_list[index + 1 :]
  string = ""
  for i in info:
    if i.startswith("%") or i == "":
      break
    else:
      string = string + i + "\n"
     
  info_list.append(string)
  
  index = package_desc_list.index("%URL%")
  info = package_desc_list[index + 1]
  info_list.append(info)
  
  index = package_desc_list.index("%PACKAGER%")
  info = package_desc_list[index + 1]
  info_list.append(info)
  
  index = package_desc_list.index("%BUILDDATE%")
  info = package_desc_list[index + 1]
  info_list.append(info)
  
  index = package_desc_list.index("%INSTALLDATE%")
  info = package_desc_list[index + 1]
  info_list.append(info)
  
  index = package_desc_list.index("%SIZE%")
  size = package_desc_list[index + 1]
  size = int(size)
  if size < 1048576:
    size = str(size / 1024)
    pref = " KB"
  else:
    size = decimal.Decimal(size) / decimal.Decimal(1048576)
    size = str(size.quantize(decimal.Decimal(".1")))
    pref = " MB"
  
  string = size + pref
  info_list.append(string)
  
  index = package_desc_list.index("%REASON%")
  info = package_desc_list[index + 1]
  if info == "0":
    string = "Explicitly installed"
    info_list.append(string)
  else:
    string = "Installed as dependency"
    info_list.append(string)
    
  index = package_depends_list.index("%DEPENDS%")
  info = package_depends_list[index + 1 :]
  dep_list = []
  for i in info:
    if i.startswith("%") or i == "":
      break
    else:
      dep_list.append(i)
  
  index = package_depends_list.index("%REQUIREDBY%")
  info = package_depends_list[index + 1 :]
  require_list = []
  for i in info:
    if i.startswith("%") or i == "":
      break
    else:
      require_list.append(i)
      
  return info_list, dep_list, require_list


# Local size
def loc_size():
  dir_list = os.listdir(root_dir + "local")
  size = 0
  for package in dir_list:
    try:
      file = open(root_dir + "local/" + package +"/desc", "r")
      file_str = file.read()
      file.close()
      desc_list = file_str.splitlines()
      size = size + int(desc_list[desc_list.index("%SIZE%") + 1])
    except:
      pass
  
  if size < 1048576:
    size = str(size / 1024)
    pref = " KB"
  else:
    size = decimal.Decimal(size) / decimal.Decimal(1048576)
    size = str(size.quantize(decimal.Decimal(".1")))
    pref = " MB"
    
  return size + pref


# Package info
def pack_info(name, server_list):
  if name == "":
    return None
  
  retcode, repo, package, name, cache = exist_check(name, server_list)
  if retcode == "0":
    return "0"
  
  package_path = root_dir + repo + "/" + package
  
  file_desc = open(package_path + "/desc", "r")
  package_desc = file_desc.read()
  file_desc.close()
  file_depends = open(package_path + "/depends", "r")
  package_depends = file_depends.read()
  file_depends.close()
  package_desc_list = package_desc.splitlines()
  package_depends_list = package_depends.splitlines()
  
  info_list = []
  index = package_desc_list.index("%NAME%")
  info = package_desc_list[index + 1]
  info_list.append(info)

  index = package_desc_list.index("%VERSION%")
  info = package_desc_list[index + 1]
  info_list.append(info)

  index = package_desc_list.index("%DESC%")
  index_next = package_desc_list.index("%CSIZE%")
  info = package_desc_list[index + 1 : index_next]
  string = ""
  for i in info:
    if i.startswith("%") or i == "":
      break
    else:
      string = string + i + "\n"
  info_list.append(string)
  
  index = package_desc_list.index("%CSIZE%")
  size = package_desc_list[index + 1]
  size = int(size)
  if size < 1048576:
    size = str(size / 1024)
    pref = " KB"
  else:
    size = decimal.Decimal(size) / decimal.Decimal(1048576)
    size = str(size.quantize(decimal.Decimal(".1")))
    pref = " MB"
  info = size + pref
  info_list.append(info)
  
  dep_list = []
  index = package_depends_list.index("%DEPENDS%")
  info = package_depends_list[index + 1 :]
  for i in info:
    if i.startswith("%") or i == "":
      break
    else:
      dep_list.append(i)
      
  return info_list, dep_list


# Optimize packagedatabase
def opt_packdb():
  tar = tarfile.open(root_dir + "packdb.tar", "w")
  tar.add(root_dir)
  tar.close()

  tar = tarfile.open(root_dir + "packdb.tar", "r")
  for i in tar:
    tar.extract(i, "/")

  tar.close()


  
