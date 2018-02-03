# Assembly  shared memory
STAR stores the transcriptome in shared memory so that concurrent STAR processes using the same assembly can share, minimizing RAM cost. This is all done by STAR automatically, but there's a few cases where you will want to manually clear/free the memory.

## Clearing shared memoryy

Clear shared memory by running `ipcs`. In the printed list, there should be objects listed, some with large number of bytes (it may not be that big if STAR crashed while creating the shared memory assembly.) If you want to get rid of an assembly you're no longer using, copy the key listed next to it and type in `ipcrm -M <KEY>`

Example:
```
mbelmadani@smithers:~$ ipcs

------ Message Queues --------
key        msqid      owner      perms      used-bytes   messages

------ Shared Memory Segments --------
key        shmid      owner      perms      bytes      nattch     status
0x172a829a 454688768  mbelmadani 666        1          1
0x172a8299 454721537  mbelmadani 666        26606420760 1
0x172a5f2f 454623234  mbelmadani 666        1          0
0x172a5f2e 454656003  mbelmadani 666        1590673903 0

mbelmadani@smithers:~$ ipcrm -M 0x172a8299
mbelmadani@smithers:~$ ipcrm -M 0x172a5f2e

```

If a previous STAR processed crashed while creating the segment, then it may cause some unexpected issues downstream. It's best to clear the memory and STAR will take care of creating it next time it is called.
