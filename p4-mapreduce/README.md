# [EECS 485 Project 4: Map Reduce Implementation](https://eecs485staff.github.io/p4-mapreduce/#mapping-worker)

Implement a __MapReduce framework__ in __Python__ inspired by Google’s original MapReduce paper. The framework executes MapReduce programs with __distributed processing__ on a cluster of computers.

The MapReduce framework consists of two major pieces of code. A __Manager__ listens for user-submitted MapReduce jobs and distributes the work among Workers. Multiple __Worker__ instances receive instructions from the Manager and execute map and reduce tasks that combine to form a MapReduce program.

Using __socket programming__ for communication between Manager process and Worker processes, and using __multithreading programming__ to handle job queue and implement __fault tolerance__.
