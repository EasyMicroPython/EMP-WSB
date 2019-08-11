EMP_LOGO = r"""
 ______     __    __     ______   __     __     ______     ______    
/\  ___\   /\ "-./  \   /\  == \ /\ \  _ \ \   /\  ___\   /\  == \   
\ \  __\   \ \ \-./\ \  \ \  _-/ \ \ \/ ".\ \  \ \___  \  \ \  __<   
 \ \_____\  \ \_\ \ \_\  \ \_\    \ \__/".~\_\  \/\_____\  \ \_____\ 
  \/_____/   \/_/  \/_/   \/_/     \/_/   \/_/   \/_____/   \/_____/
"""


EMP_INFOS = """
wsb plugin running at:
    - local: http://localhost:%s
"""


def print_emp_infos(port):
    print(EMP_LOGO)
    print(EMP_INFOS % port)
