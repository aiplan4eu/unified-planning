import unified_planning as up  
from unified_planning.shortcuts import *     
from typing import List

def greeting(num: int) -> List["up.model.Object"]:
    #return  "ciao "+name
    
    Location = UserType('Location')

    NLOC = 10
    locations = [up.model.Object('l%s' % i, Location) for i in range(NLOC)]
    return locations
    

