from gem5.utils.requires import requires
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import MESITwoLevelCacheHierarchy
from gem5.components.processors.simple_switchable_processor import SimpleSwitchableProcessor
from gem5.coherence_protocol import CoherenceProtocol
from gem5.isas import ISA
from gem5.components.processors.cpu_types import CPUTypes
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent

requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL,
)

cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="32KiB",
    l1d_assoc=8,
    l1i_size="32KiB",
    l1i_assoc=8,
    l2_size="256KiB",
    l2_assoc=16,
    num_l2_banks=1
)

memory=SingleChannelDDR3_1600(size="2GiB") # due to known X86Board limitations, memory system greater than 3GiB cannot be used

processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.ATOMIC,
    switch_core_type=CPUTypes.TIMING,
    num_cores=2,
    isa=ISA.X86
)

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy
)

command = "m5 exit;" \
        + "echo 'This is running on Timing CPU cores.';" \
        + "sleep 1;" \
        + "m5 exit;"

"""
The x86-ubuntu-18.04-img has been designed to boot the OS, automaticall login, and run the m5 readfile. The m5 readfile
will read a fileand execute it. The contents of this file are specified via the 'readfile_contents' parameter.
Therefore the value of 'readfile_contents' will be executed on system startup. Note: 'readfile_contents' is an optional
argument. If it is not specified in 'set_kernel_disk_workload' the simulation will exit after boot. This behavior is
specific to the x86-ubuntu-18.04-img disk image and is not true for all disk images.
"""

"""
The script first runs 'm5 exit'. This temporarily exits the simulation allowing us to switch the CPUs from ATOMIC to
TIMING. Then, when the simulation is resumed, the 'echo' and 'sleep' statements are executed (on the TIMING CPUs) and
'm5 exit' is called again, thus exiting and completing the simulation. Users may inspect m5out/system.pc.com_1.device
to see the echo output.
"""

board.set_kernel_disk_workload(
    kernel=obtain_resource("x86-linux-kernel-5.4.49"),
    disk_image=obtain_resource("x86-ubuntu-18.04-img"),
    readfile_contents=command
)

"""
The 'on_exit_event' argument can be used to override default behavior. The 'm5 exit' command triggers an 'EXIT' exit
event in the 'Simulator' module. By default, this exits the simulation run completely. In this case, we want the first
'm5 exit' call to switch processors from ATOMIC to TIMING cores.

The 'on_exit-event' parametr is a Python dictionary of exit events and Python generators. Here, we are setting
'ExitEvent.Exit' to the generator '(fun() for func in [processor.switch])'. This means the 'processor.switch' function
is called on the first yield of the generator (that is, on the first instance of 'm5 exit'). After this, the generator
is exhausted and the 'Simulator' module will return to the default 'Exit' exit event behavior.
"""

simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.EXIT : (func() for func in [processor.switch]),
    }
)
simulator.run()