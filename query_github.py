# Github-specific version update checker
# Two functions
# get_version()
# get_changelog()

def get_version(dep_id=None):
    verinfo = {}
    print('dep_id = {}'.format(dep_id)) 
    verinfo['version'] = '1.2.3'
    return(verinfo)
    

def get_changelog(ref_ver_data, new_ver_data):
    changelog = 'No changelog'
    return(changelog)
