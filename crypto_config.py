from config import *

import requests

from charm.toolbox.pairinggroup import PairingGroup
from charm.schemes.abenc.abenc_bsw07 import CPabe_BSW07
from charm.adapters.abenc_adapt_hybrid import HybridABEnc 

from charm.core.engine.util import objectToBytes, bytesToObject

policy_length = 16
key_size = 8

groupObj = PairingGroup('SS512')
cpabe = CPabe_BSW07(groupObj)
hybrid_abe = HybridABEnc(cpabe, groupObj)

master_key_file_name = "master_key.json"
