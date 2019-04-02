import os
import sys
import marshal
import array

try:
    import cPickle as pickle
except:
    import pickle

#Takes a messesge and returns the ASCII huffman code
def encode(msg):

    freq = {} #This dictionary will hold the char and it's frequency
    #This simple loop will just increase the freq count every time a char is repeated
    for ch in msg:
        freq[ch] = freq.get(ch, 0) + 1
    #Get the individual non-repeating characters
    data = freq.keys()
    rawData = [] #This will hold the rough tree

    for dat in data:
        rawData.append((freq[dat], dat))#Creates the initial tree

    rawData.sort()#First sort after making the tree

    #This loop will comtinue as a long as there exist two elements that have not been combined into
    #the tree. When this loop terminates it means all elements are in a tree based off their frequency
    while len(rawData) > 1:
        #get the lowest two entries
        lowestTwo = tuple(rawData[0:2])
        #Then we get the remaining elements fron the data
        theRest = rawData[2:]
        #add the two lowest frequencies together
        temp = lowestTwo[0][0] + lowestTwo[1][0]
        #Now we re-add the combined nodes to the main list
        rawData = theRest + [(temp, lowestTwo)]
        #One more sort
        # rawData.sort()
        max = len(rawData) - 1
        rawData = quickSort(rawData, 0, max) #Quicksort because the built in sorting function wasn't working

    rawData = rawData[0]#getting just the tuple

    #Trimming off the numbers from the list
    dataTree = trim(rawData)

    codex = {} #This will be the decoder ring where we keep the master code list

    #This function makes the codes
    codex = codemaker(dataTree)


    #Now to encode the message
    nuMsg = "" #This will hold the encoded message
    for char in msg:
        nuMsg += codex[char]

    return nuMsg, codex

#This is a recursive function that will call itself to go through the tree and trim off the freq. count from the
#list
def trim(data):
    temp = data[1] #ignore the first freq count
    #If the obj type is not a tuple return that
    if not isinstance(temp, tuple):
        return temp
    #If the obj is a tuple
    else:
        #trim the two leaves
        return(trim(temp[0]), trim(temp[1]))

#Quicksort editied to work with the frequency values
def quickSort(list, low, high):
    if low < high:
        pi = quickPart(list, low, high)
        quickSort(list, low, pi -1)
        quickSort(list, pi + 1, high)
    return list
#Edited to work with the frequency values
def quickPart(list, low, high):
    i = low - 1
    pivot = list[high]
    for j in range(low, high):
        if list[j][0] < pivot[0]:
            i = i + 1
            list[i], list[j] = list[j], list[i]
    list[i + 1], list[high] = list[high], list[i + 1]
    return (i + 1)

#This is a sort of shell function that will work similar to trim but assign codes instead of removing freq. values
def codemaker(tree):
    codex = {} #This will hold the codes made from the tree

    pattern = "" #We hold pattern as a string to make concatination easier then if it was an int
    #This is a recursive helper function
    codex = codeHelper(tree, codex, pattern)

    return codex
#recursive helper function
def codeHelper(tree, codex, code):
    #If this is true that means we are at the leaf and have the code for that speecific node
    #We can then add that node to the dictionary
    if not isinstance(tree, tuple):
        codex[tree] = code
    #If it is still a tuple, then we call the function on the left and right sides adding a "1" or "0" based
    #on the side of the tree used
    else:
        codeHelper(tree[0], codex, code + "0")#left side
        codeHelper(tree[1], codex, code + "1")#right side
    return codex

def decode(msg, decoderRing):

    # nuMsg = bytearray() #This will hold the decoded message
    nuMsg = array.array('B') #This will hold the decoded message

    #Get our codes and characters seperated
    codes = list(decoderRing.items())

    #Now we will loop through the message until we find a string that matches our decoderRing
    i = 0
    j = i + 1
    #While j is less then the length of the encoded message, we will increase j and i to take a substring of the messgae
    #and compare it to the codes that are in the codebook. When a code is found we set i to j and start over from the new i
    #When the loop terminates that means that part of the message does not exist in our codebook and decoding is done
    while j <= len(msg):
        for k in range(len(codes)):
            if msg[i:j] == codes[k][1]:
                nuMsg.append(codes[k][0])#appends the byte to the output array
                i += j - i #sets i to next chunk of code
                j = i
                break
        j += 1

    return nuMsg

def compress(msg):
    codedMsg, codex = encode(msg)

    #Pad encoded text
    padding = 8 - len(codedMsg) % 8 #This adds enough padding to make the message perfectly fit in a whole # of bytes

    #Add an entry to the codex with the amount of padding done
    nuVal = {"pad": padding}
    codex.update(nuVal)

    for i in range(padding):
        codedMsg += "0"#pads the message with 0's

    compressed = bytearray()
    for i in range(0, len(codedMsg), 8):
        byte = codedMsg[i:i+8]#takes 8 characters to pack into a byte
        compressed.append(int(byte,2))#packs the characters into the bytearray into a byte

    return compressed, codex

def decompress(msg, decoderRing):

    # Represent the message as an array
    byteArray = array.array('B',msg)

    rawMsg = ""#holds the raw message

    for bit in byteArray:
        bits = bin(bit)[2:].rjust(8, '0')#turns the bytes into a string of 1s and 0s
        rawMsg += bits

    #removing the padding using the dictionary entry
    padding = decoderRing.get("pad")
    finMsg = rawMsg[0:len(rawMsg) - padding]

    finMsg = decode(finMsg, decoderRing)#final decode

    return finMsg


def usage():
    sys.stderr.write("Usage: {} [-c|-d|-v|-w] infile outfile\n".format(sys.argv[0]))
    exit(1)

if __name__=='__main__':
    if len(sys.argv) != 4:
        usage()
    opt = sys.argv[1]
    compressing = False
    decompressing = False
    encoding = False
    decoding = False
    if opt == "-c":
        compressing = True
    elif opt == "-d":
        decompressing = True
    elif opt == "-v":
        encoding = True
    elif opt == "-w":
        decoding = True
    else:
        usage()

    infile = sys.argv[2]
    outfile = sys.argv[3]
    assert os.path.exists(infile)

    if compressing or encoding:
        fp = open(infile, 'rb')
        msg = fp.read()
        fp.close()
        if compressing:
            compr, decoder = compress(msg)
            fcompressed = open(outfile, 'wb')
            marshal.dump((pickle.dumps(decoder), compr), fcompressed)
            fcompressed.close()
        else:
            enc, decoder = encode(msg)
            print(enc)
            fcompressed = open(outfile, 'wb')
            marshal.dump((pickle.dumps(decoder), enc), fcompressed)
            fcompressed.close()
    else:
        fp = open(infile, 'rb')
        pickleRick, compr = marshal.load(fp)
        decoder = pickle.loads(pickleRick)
        fp.close()
        if decompressing:
            msg = decompress(compr, decoder)
        else:
            msg = decode(compr, decoder)
            print(msg)
        fp = open(outfile, 'wb')
        fp.write(msg)
        fp.close()