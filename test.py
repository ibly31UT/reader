#experimenting with pycrypto. this runs on the lab machines.



from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random
import Crypto.Random
import hashlib

# http://eli.thegreenplace.net/2010/06/25/aes-encryption-of-files-in-python-with-pycrypto

SALT_SIZE = 16
#key = hashlib.sha256('0123456789abcdef').digest() #password should be hashed

#still need to think about padding

password = '01234567890abcdef'
salt = Crypto.Random.get_random_bytes(SALT_SIZE) #randomly generate salt
prekey = SHA256.new()
prekey.update(password + salt) #hash the password and salt together


key = prekey.digest() #password is now a hash...not sure details of digest
rndfile = Random.new()

#IV = ''.join(chr(random.randint(0, 0xFF)) for i in range(16)) #16 * '\x00' # Initialization vector: discussed later

IV = ''.join(rndfile.read(16)) #generate random initialization vector
mode = AES.MODE_CBC #cipher block chaining
encryptor = AES.new(key, mode, IV=IV)

text = 'j' * 64 + 'i' * 128 #message to encrypt
#text2 = hashlib.sha256(text).digest()
ciphertextwithsalt = salt + encryptor.encrypt(text) #prepend salt
print text 
print ciphertextwithsalt

ciphertextsanssalt = ciphertextwithsalt[SALT_SIZE:] #take off salt 

decryptor = AES.new(key, mode, IV=IV)
plain = decryptor.decrypt(ciphertextsanssalt)
print plain




# http://stackoverflow.com/questions/6425131/encrypt-decrypt-data-in-python-with-salt
# this source also is encrypting a file, which may be helpful
# http://www.pythonforbeginners.com/files/reading-and-writing-files-in-python
