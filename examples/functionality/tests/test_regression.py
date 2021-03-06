# A set of regression tests for open issues

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ReadOnly
from cocotb.result import TestFailure
from cocotb.binary import BinaryValue

@cocotb.coroutine
def send_data(dut):
    dut.stream_in_valid = 1
    yield RisingEdge(dut.clk)
    dut.stream_in_valid = 0


@cocotb.coroutine
def monitor(dut):
    for i in range(4):
        yield RisingEdge(dut.clk)
    yield ReadOnly()
    if not dut.stream_in_valid.value.integer:
        raise TestFailure("stream_in_valid should be high on the 5th cycle")


@cocotb.test()
def issue_120_scheduling(dut):

    cocotb.fork(Clock(dut.clk, 2500).start())
    cocotb.fork(monitor(dut))
    yield RisingEdge(dut.clk)

    # First attempt, not from coroutine - works as expected
    for i in range(2):
        dut.stream_in_valid = 1
        yield RisingEdge(dut.clk)
        dut.stream_in_valid = 0

    yield RisingEdge(dut.clk)

    # Failure - we don't drive valid on the rising edge even though
    # behaviour should be identical to the above
    yield send_data(dut)
    dut.stream_in_valid = 1
    yield RisingEdge(dut.clk)
    dut.stream_in_valid = 0

    yield RisingEdge(dut.clk)
   


@cocotb.test()
def issue_142_overflow_error(dut):
    """Tranparently convert ints too long to pass
       through the GPI interface natively into BinaryValues"""
    cocotb.fork(Clock(dut.clk, 2500).start())

    def _compare(value):
        if int(dut.stream_in_data_wide.value) != int(value):
            raise TestFailure("Expecting 0x%x but got 0x%x on %s" % (
                int(value), int(dut.stream_in_data_wide.value), 
                str(dut.stream_in_data_wide)))

    # Wider values are transparently converted to BinaryValues
    for value in [0, 0x7FFFFFFF, 0x7FFFFFFFFFFF, BinaryValue(0x7FFFFFFFFFFFFF)]:

        dut.stream_in_data_wide <= value
        yield RisingEdge(dut.clk)
        _compare(value)
        dut.stream_in_data_wide = value
        yield RisingEdge(dut.clk)
        _compare(value)

