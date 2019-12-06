#include <stdlib.h>
#include <stdio.h>
#include <sys/shm.h>
#include <assert.h>

int main ()
{
    int ret;
    struct shmid_ds shm_info_buf;

    ret = EXIT_SUCCESS;

    int max_shm_kid = shmctl (0, SHM_INFO, &shm_info_buf);

    int shm_kid;
    for (shm_kid = max_shm_kid; shm_kid >= 0; shm_kid--)
    {
        struct shmid_ds buf;

        int shm_id = shmctl (shm_kid, SHM_STAT, &buf);

        if (shm_id == -1)
            continue;

        if (buf.shm_nattch == 0)
        {
            printf ("Clearing unused shared memory segment %d.\n", shm_id);
            if (shmctl (shm_id, IPC_RMID, NULL) != 0)
            {
                printf ("failed to remove %d.\n");
                ret = EXIT_FAILURE;
            }
        }
    }

    return ret;
}
