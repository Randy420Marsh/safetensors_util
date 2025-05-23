import os, sys, json
from safetensors_file import SafeTensorsFile

def _need_force_overwrite(output_file:str,cmdLine:dict) -> bool:
    if cmdLine["force_overwrite"]==False:
        if os.path.exists(output_file):
            print(f'output file "{output_file}" already exists, use -f flag to force overwrite',file=sys.stderr)
            return True
    return False

def WriteMetadataToHeader(cmdLine:dict,in_st_file:str,in_json_file:str,output_file:str) -> int:
    if _need_force_overwrite(output_file,cmdLine): return -1

    with open(in_json_file,"rt") as f:
        inmeta=json.load(f)
    if not "__metadata__" in inmeta:
        print(f"file {in_json_file} does not contain a top-level __metadata__ item",file=sys.stderr)
        #json.dump(inmeta,fp=sys.stdout,indent=2)
        return -2
    inmeta=inmeta["__metadata__"] #keep only metadata
    #json.dump(inmeta,fp=sys.stdout,indent=2)

    s=SafeTensorsFile.open_file(in_st_file)
    js=s.get_header()

    if inmeta==[]:
        js.pop("__metadata__",0)
        print("loaded __metadata__ is an empty list, output file will not contain __metadata__ in header")
    else:
        print("adding __metadata__ to header:")
        json.dump(inmeta,fp=sys.stdout,indent=2)
        if isinstance(inmeta,dict):
            for k in inmeta:
                inmeta[k]=str(inmeta[k])
        else:
            inmeta=str(inmeta)
        #js["__metadata__"]=json.dumps(inmeta,ensure_ascii=False)
        js["__metadata__"]=inmeta
        print()

    newhdrbuf=json.dumps(js,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    newhdrlen:int=int(len(newhdrbuf))
    pad:int=((newhdrlen+7)&(~7))-newhdrlen #pad to multiple of 8

    with open(output_file,"wb") as f:
        f.write(int(newhdrlen+pad).to_bytes(8,'little'))
        f.write(newhdrbuf)
        if pad>0: f.write(bytearray([32]*pad))
        i:int=s.copy_data_to_file(f)
    if i==0:
        print(f"file {output_file} saved successfully")
    else:
        print(f"error {i} occurred when writing to file {output_file}")
    return i

def PrintHeader(cmdLine:dict,input_file:str) -> int:
    s=SafeTensorsFile.open_file(input_file,cmdLine['quiet'])
    js=s.get_header()

    # All the .safetensors files I've seen have long key names, and as a result,
    # neither json nor pprint package prints text in very readable format,
    # so we print it ourselves, putting key name & value on one long line.
    # Note the print out is in Python format, not valid JSON format.
    firstKey=True
    print("{")
    for key in js:
        if firstKey:
            firstKey=False
        else:
            print(",")
        json.dump(key,fp=sys.stdout,ensure_ascii=False,separators=(',',':'))
        print(": ",end='')
        json.dump(js[key],fp=sys.stdout,ensure_ascii=False,separators=(',',':'))
    print("\n}")
    return 0

def _ParseMore(d:dict):
    '''Basically try to turn this:

        "ss_dataset_dirs":"{\"abc\": {\"n_repeats\": 2, \"img_count\": 60}}",

    into this:

        "ss_dataset_dirs":{
         "abc":{
          "n_repeats":2,
          "img_count":60
         }
        },

    '''
    for key in d:
        value=d[key]
        #print("+++",key,value,type(value),"+++",sep='|')
        if isinstance(value,str):
            try:
                v2=json.loads(value)
                d[key]=v2
                value=v2
            except json.JSONDecodeError as e:
                pass
        if isinstance(value,dict):
            _ParseMore(value)

def PrintMetadata(cmdLine:dict,input_file:str) -> int:
    with SafeTensorsFile.open_file(input_file,cmdLine['quiet']) as s:
        js=s.get_header()

        if not "__metadata__" in js:
            print("file header does not contain a __metadata__ item",file=sys.stderr)
            return -2

        md=js["__metadata__"]
        if cmdLine['parse_more']:
            _ParseMore(md)
        json.dump({"__metadata__":md},fp=sys.stdout,ensure_ascii=False,separators=(',',':'),indent=1)
    return 0

def HeaderKeysToLists(cmdLine:dict,input_file:str) -> int:
    s=SafeTensorsFile.open_file(input_file,cmdLine['quiet'])
    js=s.get_header()

    _lora_keys:list[tuple(str,bool)]=[] # use list to sort by name
    for key in js:
        if key=='__metadata__': continue
        v=js[key]
        isScalar=False
        if isinstance(v,dict):
            if 'shape' in v:
                if 0==len(v['shape']):
                    isScalar=True
        _lora_keys.append((key,isScalar))
    _lora_keys.sort(key=lambda x:x[0])

    def printkeylist(kl):
        firstKey=True
        for key in kl:
            if firstKey: firstKey=False
            else: print(",")
            print(key,end='')
        print()

    print("# use list to keep insertion order")
    print("_lora_keys:list[tuple[str,bool]]=[")
    printkeylist(_lora_keys)
    print("]")

    return 0


def ExtractHeader(cmdLine:dict,input_file:str,output_file:str)->int:
    if _need_force_overwrite(output_file,cmdLine): return -1

    s=SafeTensorsFile.open_file(input_file,parseHeader=False)
    if s.error!=0: return s.error

    hdrbuf=s.hdrbuf
    s.close_file() #close it in case user wants to write back to input_file itself
    with open(output_file,"wb") as fo:
        wn=fo.write(hdrbuf)
        if wn!=len(hdrbuf):
            print(f"write output file failed, tried to write {len(hdrbuf)} bytes, only wrote {wn} bytes",file=sys.stderr)
            return -1
    print(f"raw header saved to file {output_file}")
    return 0


def _CheckLoRA_internal(s:SafeTensorsFile)->int:
    import lora_keys_sd15 as lora_keys
    js=s.get_header()
    set_scalar=set()
    set_nonscalar=set()
    for x in lora_keys._lora_keys:
        if x[1]==True: set_scalar.add(x[0])
        else: set_nonscalar.add(x[0])

    bad_unknowns:list[str]=[] # unrecognized keys
    bad_scalars:list[str]=[] #bad scalar
    bad_nonscalars:list[str]=[] #bad nonscalar
    for key in js:
        if key in set_nonscalar:
            if js[key]['shape']==[]: bad_nonscalars.append(key)
            set_nonscalar.remove(key)
        elif key in set_scalar:
            if js[key]['shape']!=[]: bad_scalars.append(key)
            set_scalar.remove(key)
        else:
            if "__metadata__"!=key:
                bad_unknowns.append(key)

    hasError=False

    if len(bad_unknowns)!=0:
        print("INFO: unrecognized items:")
        for x in bad_unknowns: print(" ",x)
        #hasError=True

    if len(set_scalar)>0:
        print("missing scalar keys:")
        for x in set_scalar: print(" ",x)
        hasError=True
    if len(set_nonscalar)>0:
        print("missing nonscalar keys:")
        for x in set_nonscalar: print(" ",x)
        hasError=True

    if len(bad_scalars)!=0:
        print("keys expected to be scalar but are nonscalar:")
        for x in bad_scalars: print(" ",x)
        hasError=True

    if len(bad_nonscalars)!=0:
        print("keys expected to be nonscalar but are scalar:")
        for x in bad_nonscalars: print(" ",x)
        hasError=True

    return (1 if hasError else 0)

def CheckLoRA(cmdLine:dict,input_file:str)->int:
    s=SafeTensorsFile.open_file(input_file)
    i:int=_CheckLoRA_internal(s)
    if i==0: print("looks like an OK SD 1.x LoRA file")
    return 0

def ExtractData(cmdLine:dict,input_file:str,key_name:str,output_file:str)->int:
    if _need_force_overwrite(output_file,cmdLine): return -1

    s=SafeTensorsFile.open_file(input_file,cmdLine['quiet'])
    if s.error!=0: return s.error

    bindata=s.load_one_tensor(key_name)
    s.close_file() #close it just in case user wants to write back to input_file itself
    if bindata is None:
        print(f'key "{key_name}" not found in header (key names are case-sensitive)',file=sys.stderr)
        return -1

    with open(output_file,"wb") as fo:
        wn=fo.write(bindata)
        if wn!=len(bindata):
            print(f"write output file failed, tried to write {len(bindata)} bytes, only wrote {wn} bytes",file=sys.stderr)
            return -1
    if cmdLine['quiet']==False: print(f"{key_name} saved to {output_file}, len={wn}")
    return 0

def CheckHeader(cmdLine:dict,input_file:str)->int:
    rv:int=0
    s=SafeTensorsFile.open_file(input_file)
    maxoffset=int(s.st.st_size-8-s.headerlen)
    h=s.get_header()
    for k,v in h.items():
        if k=='__metadata__': continue
        #print(k,v)
        msgs=[]
        if v['data_offsets'][0]>maxoffset or v['data_offsets'][1]>maxoffset:
            msgs.append("data past end of file")
        lenv=int(v['data_offsets'][1]-v['data_offsets'][0])
        items=int(1)
        for i in v['shape']: items*=int(i)

        if v['dtype']=="F16":
            item_size=int(2)
        elif v['dtype']=="F32":
            item_size=int(4)
        elif v['dtype']=="F64":
            item_size=int(8)
        else:
            item_size=int(0)

        if item_size==0:
            if (lenv % items)!=0:
                msgs.append("length not integral multiples of item count")
        else:
            len2=item_size*items
            if len2!=lenv:
                msgs.append(f"length should be {len2}, actual length is {lenv}")

        if len(msgs) > 0:
            print(f"error in f{k}:{v}:")
            for m in msgs:
                print(" * ",m,sep='')
            rv=1

    if rv==0: print("no error found")
    return rv
