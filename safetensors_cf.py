import os, sys, json, copy
from safetensors_file import SafeTensorsFile
import safetensors_worker
import numpy as np

def adjust_new_header(keys:list[str],newhdr:dict)->int:
    cur_offset=0; savedbytes=0
    for k in keys:
        v=newhdr[k]
        dl=v['data_offsets'][1]-v['data_offsets'][0]
        if v['dtype']=='F32':
            dl=dl//2; savedbytes+=dl
            v['dtype']='F16'
        elif v['dtype']=='F64':
            dl=dl//4; savedbytes+=dl*3
            v['dtype']='F16'
        v['data_offsets'][0]=cur_offset
        cur_offset+=dl
        v['data_offsets'][1]=cur_offset
        newhdr[k]=v
    return savedbytes

def convert_to_float16_clamped(float_array):
    f16_info = np.finfo(np.float16)
    result = float_array.astype(np.float16)
    result = np.where(np.isposinf(result), f16_info.max, result)
    result = np.where(np.isneginf(result), f16_info.min, result)
    return result

def CompactFloat(cmdLine:dict,input_file:str,output_file:str)->int:
    if safetensors_worker._need_force_overwrite(output_file,cmdLine): return -1

    s=SafeTensorsFile.open_file(input_file,cmdLine['quiet'])
    if s.error!=0: return s.error

    hdr=s.get_header()
    newhdr=copy.deepcopy(hdr) #create a new header
    if "__metadata__" in hdr:
        newhdr["__metadata__"]=hdr["__metadata__"]
        hdr.pop("__metadata__")

    keys=list(hdr.keys())
    keys.sort(key=lambda x:hdr[x]['data_offsets'][0]) #sort keys by starting offset
    tensorsaves=adjust_new_header(keys,newhdr)

    #for k in keys:
    #    if hdr[k]['dtype']=='F32' or hdr[k]['dtype']=='F64':
    #        print("---",hdr[k],'->',newhdr[k])
    #print(newhdr)
    print("size reduction from converting F32 and F64 to F16:",tensorsaves)

    newhdrbuf=json.dumps(newhdr,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    newhdrlen:int=int(len(newhdrbuf))
    pad:int=((newhdrlen+7)&(~7))-newhdrlen #pad to multiple of 8

    with open(output_file,"wb") as fo:
        fo.write(int(newhdrlen+pad).to_bytes(8,'little'))
        fo.write(newhdrbuf)
        if pad>0: fo.write(bytearray([32]*pad))
        for k in keys:
            buf=s.load_one_tensor(k)
            #print(hdr[k],len(buf))
            if hdr[k]['dtype']=='F32' or hdr[k]['dtype']=='F64':
                intype=np.float32 if hdr[k]['dtype']=='F32' else np.float64
                data=np.frombuffer(buf,dtype=intype)
                df16=convert_to_float16_clamped(data)
                df16.tofile(fo)
            else:
                fo.write(buf)
        print(f"final file size: {fo.tell()} vs {s.st.st_size}, dif={s.st.st_size-fo.tell()}")

    return 0
