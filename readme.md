### Features

This is a light-weight utility program for [safetensors files](https://github.com/huggingface/safetensors "safetensors files") written in Python only (no major external dependencies). Currently it can do the following:

    Usage: safetensors_util.py [OPTIONS] COMMAND [ARGS]...

    Options:
      --version    Show the version and exit.
      -q, --quiet  quiet mode, don't print informational stuff
      --help       Show this message and exit.

    Commands:
      cf           compact F32 and F64 tensors to F16
      checkhdr     check header for possible errors
      checklora    see if input file is a SD 1.x LoRA file
      extractdata  extract one tensor and save to file
      extracthdr   extract file header and save to file
      header       print file header
      listkeys     print header key names (except __metadata__) as a Python list
      metadata     print only __metadata__ in file header
      writemd      read __metadata__ from json and write to safetensors file


The most useful thing is probably the read and write metadata commands. To read metadata:

        python safetensors_util.py metadata input_file.safetensors -pm

Many safetensors files, for example LoRA files, have a \_\_metadata\_\_ field that records metadata such as learning rates during training, number of epochs, number of images used, etc.

The optional **-pm** flag is meant to make \_\_metadata\_\_ more readable. Because safetensors files allow only string-to-string key-value pairs in metadata, non-string values must be quoted, for example:

        "ss_dataset_dirs":"{\"abc\": {\"n_repeats\": 2, \"img_count\": 60}}",

 The **-pm** flag tries to turn the above into this:

        "ss_dataset_dirs" : {
          "abc":{
            "n_repeats":2,
            "img_count":60
          }
        }

You can also create a JSON file containing a \_\_metadata\_\_ entry:

    {
         "__metadata__":{
              "Description": "Stable Diffusion 1.5 LoRA trained on cat pictures",
              "Trigger Words":["cat from hell","killer kitten"],
              "Base Model": "Stable Diffusion 1.5",
              "Training Info": {
                    "trainer": "modified Kohya SS",
                    "resolution":[512,512],
                    "lr":1e-6,
                    "text_lr":1e-6,
                    "schedule": "linear",
                    "text_scheduler": "linear",
                    "clip_skip": 0,
                    "regularization_images": "none"
              },
              "ss_network_alpha":16,
              "ss_network_dim":16
         }
    }

and write it to a safetensors file header using the **writemd** command:

        python safetensors_util.py writemd input.safetensors input.json output.safetensors
