import json
import re
import sys
import xml.etree.ElementTree as ET

def get_stat_value(stats, key, default=0):
    """
    Safely retrieves a numeric value from the stats dictionary.
    """
    try:
        return float(stats.get(key, default))
    except (ValueError, TypeError):
        return default

def parse_stats(stats_file):
    """
    Parses the stats.txt file and returns a dictionary of key-value pairs.
    """
    stats = {}
    with open(stats_file, 'r') as f:
        for line in f:
            if not line.strip() or '---' in line or line.startswith('End'):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0]
                value = parts[1]
                stats[key] = value
    return stats

def parse_config(config_file):
    """
    Parses the config.json file and returns a dictionary of configuration data.
    """
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    return config_data

def create_mcpat_xml(stats, config):
    """
    Creates an McPAT XML file based on the gem5 stats and config.
    """
    mcpat_template = """<?xml version="1.0"?>
    <component id="root" name="root" >
        <component id="system" name="system">
            <param name="number_of_cores" value="1"/>
            <param name="number_of_L1I_caches" value="1"/>
            <param name="number_of_L1D_caches" value="1"/>
            <param name="number_of_L2_caches" value="1"/>
            <param name="number_of_L3_caches" value="0"/>
            <param name="number_of_NoC" value="0"/>
            <param name="target_core_clockrate" value="0"/>
            <param name="total_cycles" value="0"/>
            <param name="peak_power_per_chip" value="0"/>
            <param name="total_insts" value="0"/>
            <param name="number_of_L1Directories" value="0"/>
            <param name="homogeneous_L1Directories" value="1"/>
            <component id="core0" name="core">
                <param name="clock_rate" value="0"/>
                <param name="total_inst" value="0"/>
                <param name="int_inst" value="0"/>
                <param name="fp_inst" value="0"/>
                <param name="load_inst" value="0"/>
                <param name="store_inst" value="0"/>
                <param name="committed_inst" value="0"/>
                <param name="committed_int_inst" value="0"/>
                <param name="committed_fp_inst" value="0"/>
                <param name="rob_accesses" value="0"/>
                <param name="issue_queue_accesses" value="0"/>
                <param name="int_regfile_reads" value="0"/>
                <param name="fp_regfile_reads" value="0"/>
                <param name="int_regfile_writes" value="0"/>
                <param name="fp_regfile_writes" value="0"/>
                <param name="rename_accesses" value="0"/>
                <param name="rob_reads" value="0"/>
                <param name="rob_writes" value="0"/>
                <param name="L1I_hits" value="0"/>
                <param name="L1I_misses" value="0"/>
                <param name="L1D_hits" value="0"/>
                <param name="L1D_misses" value="0"/>
                <param name="L2_hits" value="0"/>
                <param name="L2_misses" value="0"/>
                <param name="Instruction_Fetch_Buffer_reads" value="0"/>
                <param name="Instruction_Fetch_Buffer_writes" value="0"/>
                <param name="ITLB_accesses" value="0"/>
                <param name="ITLB_misses" value="0"/>
                <param name="DTLB_accesses" value="0"/>
                <param name="DTLB_misses" value="0"/>
                <param name="branch_insts" value="0"/>
                <param name="branch_mispredictions" value="0"/>
            </component>
            <component id="L1_I_cache" name="L1Icache">
                <param name="cache_size" value="0"/>
                <param name="line_size" value="0"/>
                <param name="associativity" value="0"/>
                <param name="bank" value="1"/>
                <param name="sequential_access" value="true"/>
                <param name="read_accesses" value="0"/>
                <param name="write_accesses" value="0"/>
                <param name="total_accesses" value="0"/>
                <param name="total_reads" value="0"/>
                <param name="total_writes" value="0"/>
            </component>
            <component id="L1_D_cache" name="L1Dcache">
                <param name="cache_size" value="0"/>
                <param name="line_size" value="0"/>
                <param name="associativity" value="0"/>
                <param name="bank" value="1"/>
                <param name="sequential_access" value="true"/>
                <param name="read_accesses" value="0"/>
                <param name="write_accesses" value="0"/>
                <param name="total_accesses" value="0"/>
                <param name="total_reads" value="0"/>
                <param name="total_writes" value="0"/>
            </component>
            <component id="L2_cache" name="L2cache">
                <param name="cache_size" value="0"/>
                <param name="line_size" value="0"/>
                <param name="associativity" value="0"/>
                <param name="bank" value="1"/>
                <param name="sequential_access" value="true"/>
                <param name="read_accesses" value="0"/>
                <param name="write_accesses" value="0"/>
                <param name="total_accesses" value="0"/>
                <param name="total_reads" value="0"/>
                <param name="total_writes" value="0"/>
            </component>
            <component id="main_memory" name="main_memory">
                <param name="peak_memory_bw" value="25.6"/>
                <param name="ext_dram_accesses" value="0"/>
            </component>
        </component>
    </component>
    """



    tree = ET.ElementTree(ET.fromstring(mcpat_template))
    root = tree.getroot()

    # Get cache line size from the system configuration
    cache_line_size = config.get('board', {}).get('cache_line_size', 64)

    # System parameters
    system_node = root.find(".//component[@name='system']")
    if system_node:
        total_insts = get_stat_value(stats, 'simInsts')
        system_node.find(".//param[@name='total_insts']").attrib['value'] = str(int(total_insts))
        total_cycles = get_stat_value(stats, 'board.processor.cores.core.tickCycles')
        system_node.find(".//param[@name='total_cycles']").attrib['value'] = str(int(total_cycles))
        
        # Clock rate in MHz
        clock_rate_hz = get_stat_value(stats, 'simFreq', 1000000000000)
        clock_rate_mhz = clock_rate_hz / 1000000.0
        system_node.find(".//param[@name='target_core_clockrate']").attrib['value'] = str(clock_rate_mhz)

    # Core parameters
    core_node = root.find(".//component[@name='core']")
    if core_node:
        core_node.find(".//param[@name='clock_rate']").attrib['value'] = str(clock_rate_mhz)
        # Use simInsts for total and committed instructions
        total_inst = get_stat_value(stats, 'simInsts')
        core_node.find(".//param[@name='total_inst']").attrib['value'] = str(int(total_inst))
        core_node.find(".//param[@name='committed_inst']").attrib['value'] = str(int(total_inst))
        
        # Get load and store instruction counts from the data cache stats
        load_inst = get_stat_value(stats, 'board.cache_hierarchy.l1dcaches.ReadReq.accesses::total')
        store_inst = get_stat_value(stats, 'board.cache_hierarchy.l1dcaches.WriteReq.accesses::total')
        
        core_node.find(".//param[@name='int_inst']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.int_insts', 0)))
        core_node.find(".//param[@name='fp_inst']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.fp_insts', 0)))
        core_node.find(".//param[@name='load_inst']").attrib['value'] = str(int(load_inst))
        core_node.find(".//param[@name='store_inst']").attrib['value'] = str(int(store_inst))
        core_node.find(".//param[@name='committed_int_inst']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.committed_int_insts', 0)))
        core_node.find(".//param[@name='committed_fp_inst']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.committed_fp_insts', 0)))

        # Pipeline access counts (not in stats.txt, so they will be 0)
        core_node.find(".//param[@name='rob_accesses']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.rob_accesses', 0)))
        core_node.find(".//param[@name='issue_queue_accesses']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.issue_queue_accesses', 0)))
        core_node.find(".//param[@name='int_regfile_reads']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.int_regfile_reads', 0)))
        core_node.find(".//param[@name='fp_regfile_reads']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.fp_regfile_reads', 0)))
        core_node.find(".//param[@name='int_regfile_writes']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.int_regfile_writes', 0)))
        core_node.find(".//param[@name='fp_regfile_writes']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.fp_regfile_writes', 0)))
        core_node.find(".//param[@name='rename_accesses']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.rename_accesses', 0)))
        
        core_node.find(".//param[@name='rob_reads']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.rob_reads', 0)))
        core_node.find(".//param[@name='rob_writes']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.rob_writes', 0)))

        # Cache and TLB accesses
        core_node.find(".//param[@name='L1I_hits']").attrib['value'] = str(int(get_stat_value(stats, 'board.cache_hierarchy.l1icaches.overallHits::total', 0)))
        core_node.find(".//param[@name='L1I_misses']").attrib['value'] = str(int(get_stat_value(stats, 'board.cache_hierarchy.l1icaches.overallMisses::total', 0)))
        core_node.find(".//param[@name='L1D_hits']").attrib['value'] = str(int(get_stat_value(stats, 'board.cache_hierarchy.l1dcaches.overallHits::total')))
        core_node.find(".//param[@name='L1D_misses']").attrib['value'] = str(int(get_stat_value(stats, 'board.cache_hierarchy.l1dcaches.overallMisses::total')))
        core_node.find(".//param[@name='L2_hits']").attrib['value'] = str(int(get_stat_value(stats, 'board.cache_hierarchy.l2cache.overallHits::total', 0)))
        core_node.find(".//param[@name='L2_misses']").attrib['value'] = str(int(get_stat_value(stats, 'board.cache_hierarchy.l2cache.overallMisses::total', 0)))
        
        # TLB stats (not in stats.txt, so they will be 0)
        core_node.find(".//param[@name='ITLB_accesses']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.mmu.dtb.accesses', 0)))
        core_node.find(".//param[@name='ITLB_misses']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.mmu.dtb.misses', 0)))
        core_node.find(".//param[@name='DTLB_accesses']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.mmu.itb.accesses', 0)))
        core_node.find(".//param[@name='DTLB_misses']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.mmu.itb.misses', 0)))

        # Branch Prediction
        core_node.find(".//param[@name='branch_insts']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.branchPred.condPredicted', 0)))
        core_node.find(".//param[@name='branch_mispredictions']").attrib['value'] = str(int(get_stat_value(stats, 'board.processor.cores.core.branchPred.condIncorrect', 0)))
    
    # L1I Cache parameters
    l1i_node = root.find(".//component[@name='L1Icache']")
    if l1i_node:
        try:
            l1i_config_list = config['board']['cache_hierarchy']['l1icaches']
            l1i_config = l1i_config_list[0]
            size = l1i_config['size']
            assoc = l1i_config['assoc']
            
            l1i_node.find(".//param[@name='cache_size']").attrib['value'] = str(int(size) / 1024)
            l1i_node.find(".//param[@name='line_size']").attrib['value'] = str(cache_line_size)
            l1i_node.find(".//param[@name='associativity']").attrib['value'] = str(assoc)
            
            l1i_accesses = get_stat_value(stats, 'board.cache_hierarchy.l1icaches.overallAccesses::total', 0)
            l1i_reads = get_stat_value(stats, 'board.cache_hierarchy.l1icaches.ReadReq.accesses::total', 0)
            l1i_writes = get_stat_value(stats, 'board.cache_hierarchy.l1icaches.WriteReq.accesses::total', 0)
            
            l1i_node.find(".//param[@name='total_accesses']").attrib['value'] = str(int(l1i_accesses))
            l1i_node.find(".//param[@name='total_reads']").attrib['value'] = str(int(l1i_reads))
            l1i_node.find(".//param[@name='total_writes']").attrib['value'] = str(int(l1i_writes))
        except (KeyError, IndexError):
            print("Warning: Could not find L1I cache config. Defaulting to 0.")
    
    # L1D Cache parameters
    l1d_node = root.find(".//component[@name='L1Dcache']")
    if l1d_node:
        try:
            l1d_config_list = config['board']['cache_hierarchy']['l1dcaches']
            l1d_config = l1d_config_list[0]
            size = l1d_config['size']
            assoc = l1d_config['assoc']
            
            l1d_node.find(".//param[@name='cache_size']").attrib['value'] = str(int(size) / 1024)
            l1d_node.find(".//param[@name='line_size']").attrib['value'] = str(cache_line_size)
            l1d_node.find(".//param[@name='associativity']").attrib['value'] = str(assoc)
            
            l1d_accesses = get_stat_value(stats, 'board.cache_hierarchy.l1dcaches.overallAccesses::total')
            l1d_reads = get_stat_value(stats, 'board.cache_hierarchy.l1dcaches.ReadReq.accesses::total')
            l1d_writes = get_stat_value(stats, 'board.cache_hierarchy.l1dcaches.WriteReq.accesses::total')
            
            l1d_node.find(".//param[@name='total_accesses']").attrib['value'] = str(int(l1d_accesses))
            l1d_node.find(".//param[@name='total_reads']").attrib['value'] = str(int(l1d_reads))
            l1d_node.find(".//param[@name='total_writes']").attrib['value'] = str(int(l1d_writes))
        except (KeyError, IndexError):
            print("Warning: Could not find L1D cache config. Defaulting to 0.")
    
    # L2 Cache parameters
    l2_node = root.find(".//component[@name='L2cache']")
    if l2_node:
        try:
            l2_config = config['board']['cache_hierarchy']['l2cache']
            
            size = l2_config['size']
            assoc = l2_config['assoc']
            
            l2_node.find(".//param[@name='cache_size']").attrib['value'] = str(int(size) / 1024)
            l2_node.find(".//param[@name='line_size']").attrib['value'] = str(cache_line_size)
            l2_node.find(".//param[@name='associativity']").attrib['value'] = str(assoc)
            
            l2_accesses = get_stat_value(stats, 'board.cache_hierarchy.l2cache.overallAccesses::total', 0)
            l2_reads = get_stat_value(stats, 'board.cache_hierarchy.l2cache.ReadReq.accesses::total', 0)
            l2_writes = get_stat_value(stats, 'board.cache_hierarchy.l2cache.WriteReq.accesses::total', 0)
            
            l2_node.find(".//param[@name='total_accesses']").attrib['value'] = str(int(l2_accesses))
            l2_node.find(".//param[@name='total_reads']").attrib['value'] = str(int(l2_reads))
            l2_node.find(".//param[@name='total_writes']").attrib['value'] = str(int(l2_writes))
        except KeyError:
            print("Warning: Could not find L2 cache config. Defaulting to 0.")
    
    # Main Memory
    mem_node = root.find(".//component[@name='main_memory']")
    if mem_node:
        dram_reads = get_stat_value(stats, 'board.memory.mem_ctrl.dram.numReads::total', 0)
        l1d_writebacks = get_stat_value(stats, 'board.cache_hierarchy.l1dcaches.writebacks::total', 0)
        ext_dram_accesses = dram_reads + l1d_writebacks
        mem_node.find(".//param[@name='ext_dram_accesses']").attrib['value'] = str(int(ext_dram_accesses))

    return ET.tostring(root, encoding='utf-8').decode('utf-8')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python custom_converter.py <path_to_stats.txt> <path_to_config.json>")
        sys.exit(1)
    
    stats_file = sys.argv[1]
    config_file = sys.argv[2]

    try:
        stats = parse_stats(stats_file)
        config = parse_config(config_file)
        mcpat_xml = create_mcpat_xml(stats, config)
        
        with open("mcpat_output.xml", "w") as f:
            f.write(mcpat_xml)
        
        print("Successfully generated mcpat_output.xml")
    
    except FileNotFoundError:
        print(f"Error: One or both of the files could not be found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")