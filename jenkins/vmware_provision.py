# sudo pip install pyvmomi minitest
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
import time
from contextlib import contextmanager
import threading
import argparse
import sys

VERSION = "0.1.0"

def gen_parse():
    parser = argparse.ArgumentParser( 
        description="Provision for vshpere!")
    # SafelyDestroy
    parser.add_argument('--name_key', '-n', required=True,
        help='the key word of host name')
    parser.add_argument('--action_name', '-a', required=True, 
        choices=['poweroff', 'poweron', 'clone', 'delete', 'revert'],
        help='the action, please choose one from list.')
    parser.add_argument('--thread_count', '-t', type=int, default=1, 
        help='how many threads will run')
    parser.add_argument('--iteration_count', '-i', type=int, default=1, 
        help='how many iteration will run')
    parser.add_argument('--vm_names',
        help='specify some vm names, use comma , to sperate, please set basic port. If action is clone, please set a _number at the end of name')
    parser.add_argument('--basic_port', type=int, default=7000,
        help='basic port')
    parser.add_argument('--start_num', type=int, default=0, 
        help='what is the name index from ')
    parser.add_argument('--end_num', type=int, default=-1, 
        help='what is the name index end ')
    parser.add_argument('--version', '-v', action="store_true", 
        help='current version')
    # parser.add_argument('--debug', choices=['y','n'], default='n', required=False,
    #     help='show some debug information')
    return parser


def flatten(lst):
    result = []
    for sublist in lst:
        if isinstance(sublist, list):
            for item in sublist:
                result.append(item)
        else:
            result.append(sublist)
    return result

def wait_task(task):
    while task.info.state == vim.TaskInfo.State.running:
       time.sleep(2)
    if task.info.state == vim.TaskInfo.State.success:
        print '{action_name} completed successfully, result: {result}'.format(
                action_name=task.info.descriptionId, 
                result = task.info.result)
        return task.info.result
    else:
        print '{action_name} had an error, error: {error}'.format(
                action_name=task.info.descriptionId, 
                error = task.info.error)
        return task.info.error

def SafelyDestroy(self):
    if self.runtime.powerState == 'poweredOn':
        power_off_task = self.PowerOff()
        # must wait to power off, otherwise will report error
        wait_task(power_off_task)
    return self.Destroy()

# pyVmomi.VmomiSupport.vim.VirtualMachine.SafelyDestroy = SafelyDestroy
vim.VirtualMachine.SafelyDestroy = SafelyDestroy

@contextmanager
def open_connection():
    host = 'x.x.x.x'
    user = '***'
    password = '***'
    port = 443
    try:
        service_instance = SmartConnect(host=host, user=user, pwd=password, port=port)
        print "connected to {host}".format(host=host)
        yield service_instance
    finally:
        Disconnect(service_instance)

def do_action(vm_names, action_name):
    def do(vm):
        # result = vm.PowerOn()
        # print vm.summary.guest.ipAddress
        print "{vm_name} is being {action_name}".format(
                vm_name=vm.name, action_name = action_name)
        return getattr(vm, action_name)()

    with open_connection() as service_instance:
        print "finding all virtual machines..."
        obj_view = service_instance.content.viewManager.CreateContainerView(
                service_instance.content.rootFolder,
                [vim.VirtualMachine],
                True)
        all_vms = obj_view.view
        vms = filter(lambda vm: vm.name in vm_names, all_vms)
        obj_view.Destroy()

        tasks = map(do, vms)
        tasks = flatten(tasks)

        map(wait_task, tasks)



# https://docs.python.org/3/library/contextlib.html

"""
 Get the vsphere object associated with a given text name
"""
def get_obj(content, vimtype, name):
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for item in container.view:
        if item.name == name:
            return item

# https://gist.github.com/snobear/8788977
# this one will first clone vm, then add serial port.
# when you run 10 thread count and 40 iterations, it will report error
# seems like it cannot wait finish of clone.
def clone_o(template_vm_name, datastore_name, host_system_name, vm_names, basic_port):

    with open_connection() as service_instance:
        obj_view = service_instance.content.viewManager.CreateContainerView(
                service_instance.content.rootFolder,
                [vim.VirtualMachine],
                True)
        all_vms = obj_view.view
        obj_view.Destroy()

        template_vms = filter(lambda vm: vm.name == template_vm_name, all_vms)
        if len(template_vms) <= 0:
            print "Error, cannot find the template vm: {template_vm_name}".format(
                    template_vm_name=template_vm_name)
        template_vm = template_vms[0]

        # datastores = service_instance.content.viewManager.CreateContainerView(service_instance.content.rootFolder, [vim.Datastore], True)
        datastore = get_obj(service_instance.content, [vim.Datastore], datastore_name)
        # hosts = service_instance.content.viewManager.CreateContainerView(service_instance.content.rootFolder, [vim.HostSystem], True)
        host_system = get_obj(service_instance.content, 
            [vim.HostSystem], host_system_name)
        resource_pool = host_system.parent.resourcePool

        # Relocation spec
        relospec = vim.vm.RelocateSpec()
        relospec.datastore = datastore
        relospec.pool = resource_pool
        relospec.host = host_system

        clonespec = vim.vm.CloneSpec()
        clonespec.location = relospec
        # clonespec.config = vmconf
        # clonespec.customization = customspec
        clonespec.powerOn = False
        clonespec.template = False
     
        # fire the clone task
        def do(vm_name):
            # result = vm.PowerOn()
            print "cloning {vm_name} from {template_vm_name}".format(
                    vm_name=vm_name,template_vm_name=template_vm.name)
            return template_vm.Clone(
                folder=template_vm.parent, 
                name=vm_name, 
                spec=clonespec)

            return getattr(vm, action_function)()

        ##
        tasks = map(do, vm_names)
        map(wait_task, tasks)

        add_serial_port_and_power_on(service_instance, vm_names, host_system_name, basic_port)


def clone(template_vm_name, datastore_name, host_system_name, vm_names, basic_port):

    with open_connection() as service_instance:
        obj_view = service_instance.content.viewManager.CreateContainerView(
                service_instance.content.rootFolder,
                [vim.VirtualMachine],
                True)
        all_vms = obj_view.view
        obj_view.Destroy()

        template_vms = filter(lambda vm: vm.name == template_vm_name, all_vms)
        if len(template_vms) <= 0:
            print "Error, cannot find the template vm: {template_vm_name}".format(
                    template_vm_name=template_vm_name)
        template_vm = template_vms[0]

        # datastores = service_instance.content.viewManager.CreateContainerView(service_instance.content.rootFolder, [vim.Datastore], True)
        datastore = get_obj(service_instance.content, [vim.Datastore], datastore_name)
        # hosts = service_instance.content.viewManager.CreateContainerView(service_instance.content.rootFolder, [vim.HostSystem], True)
        host_system = get_obj(service_instance.content, 
            [vim.HostSystem], host_system_name)
        resource_pool = host_system.parent.resourcePool

        # Relocation spec
        relospec = vim.vm.RelocateSpec()
        relospec.datastore = datastore
        relospec.pool = resource_pool
        relospec.host = host_system

        clonespec = vim.vm.CloneSpec()
        clonespec.location = relospec
        # clonespec.config = get_serial_port_spec(host_system_name, generate_port(vm_name, basic_port))
        # clonespec.customization = customspec
        clonespec.powerOn = True
        clonespec.template = False
     
        # fire the clone task
        def do(vm_name):
            # result = vm.PowerOn()
            print "cloning {vm_name} from {template_vm_name}".format(
                    vm_name=vm_name,template_vm_name=template_vm.name)
            clonespec.config = get_serial_port_spec(host_system_name, generate_port(vm_name, basic_port))
            return template_vm.Clone(
                folder=template_vm.parent, 
                name=vm_name, 
                spec=clonespec)


        ##
        tasks = map(do, vm_names)
        map(wait_task, tasks)




def add_serial_port_and_power_on(service_instance, vm_names, host_system_name, basic_port):
    ## 
    obj_view = service_instance.content.viewManager.CreateContainerView(
            service_instance.content.rootFolder,
            [vim.VirtualMachine],
            True)
    all_vms = obj_view.view
    vms = filter(lambda vm: vm.name in vm_names, all_vms)
    obj_view.Destroy()

    add_serial_port_tasks = [add_serial_port_for_vm(
        vm, host_system_name, generate_port(vm.name, basic_port)) for vm in vms]
    map(wait_task, add_serial_port_tasks)

    power_on_tasks = [vm.PowerOn() for vm in vms]
    map(wait_task, power_on_tasks)


def generate_port(vm_name, basic_port):
    return int(vm_name.split('_')[-1]) + basic_port

def add_serial_port_for_vm(vm, host_system_name, port):
    # host_system_name = "qa-esx107a.sun.corp.fortinet.com"
    # port = 7016

    backing = vim.vm.device.VirtualSerialPort.URIBackingInfo()
    backing.direction = "server"
    backing.serviceURI = "telnet://{host}:{port}".format(
        host=host_system_name, port=port)

    connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    connectable.allowGuestControl = True
    connectable.connected = False
    connectable.startConnected = True

    serial_port = vim.vm.device.VirtualSerialPort()
    serial_port.yieldOnPoll = True
    serial_port.connectable = connectable
    serial_port.backing = backing
    serial_port.key = -100
 
    spec_operation = vim.vm.device.VirtualDeviceSpec.Operation("add")

    uri_spec = vim.vm.device.VirtualDeviceSpec()
    uri_spec.operation = spec_operation
    uri_spec.device = serial_port

    config_spec = vim.vm.ConfigSpec()
    config_spec.deviceChange=[uri_spec]


    return vm.Reconfigure(config_spec)


def get_serial_port_spec(host_system_name, port):
    # host_system_name = "qa-esx107a.sun.corp.fortinet.com"
    # port = 7016

    backing = vim.vm.device.VirtualSerialPort.URIBackingInfo()
    backing.direction = "server"
    backing.serviceURI = "telnet://{host}:{port}".format(
        host=host_system_name, port=port)

    connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    connectable.allowGuestControl = True
    connectable.connected = False
    connectable.startConnected = True

    serial_port = vim.vm.device.VirtualSerialPort()
    serial_port.yieldOnPoll = True
    serial_port.connectable = connectable
    serial_port.backing = backing
    serial_port.key = -100
 
    spec_operation = vim.vm.device.VirtualDeviceSpec.Operation("add")

    uri_spec = vim.vm.device.VirtualDeviceSpec()
    uri_spec.operation = spec_operation
    uri_spec.device = serial_port

    config_spec = vim.vm.ConfigSpec()
    config_spec.deviceChange=[uri_spec]


    return config_spec

def do_action_worker(thread_index, thread_count,start_num, end_num, name_key, action_name):
    vm_names = generate_vm_names(thread_index, thread_count, start_num, end_num, name_key)
    # vm_names.pp()
    do_action(vm_names, action_name)


def clone_worker(thread_index, thread_count, start_num, end_num, name_key, template_vm_name, basic_port):
    vm_names = generate_vm_names(thread_index, thread_count, start_num, end_num, name_key)
    # vm_names.pp()
    datastore_name = "eq{name_key}-fortigate".format(name_key=name_key)
    host_system_name = "qa-esx{name_key}.sun.corp.fortinet.com".format(name_key=name_key)
    clone(template_vm_name, datastore_name, host_system_name, vm_names, basic_port)

def generate_vm_names(thread_index, thread_count, start_num, end_num, name_key):
    # name_key = "107a"
    # name_format = "FGT_VM_107a_0016"    
    count = end_num - start_num + 1
    iteration_count = count / thread_count
    name_format = "FGT_VM_"+name_key+"_{index_str}"
    index_str_list = [str(i*thread_count+thread_index+start_num).zfill(4) for i in range(iteration_count)]
    return [name_format.format(index_str=index_str) for index_str in index_str_list]


def main(thread_count, start_num, end_num, action_name, name_key, 
        template_vm_name=None, basic_port=None):
    (thread_count, start_num, end_num, action_name, name_key, template_vm_name, basic_port).pp()
    if action_name == 'clone':
        worker = lambda thread_index: clone_worker(
                thread_index, thread_count, start_num, end_num, 
                name_key, template_vm_name, basic_port)
    else:
        worker = lambda thread_index: do_action_worker(
                thread_index, thread_count, start_num, end_num, 
                name_key, action_name)
    print "Totally thread count: {thread_count}".format(thread_count=thread_count)
    if thread_count == 1:
        worker(0)
    else:
        [threading.Thread(target=worker, args=(i,)).start() for i in range(thread_count)]

def main_vm_names(action_name, name_key, vm_names, template_vm_name=None, basic_port=None):
    vm_names = vm_names.split(",")
    if action_name == 'clone':
        datastore_name = "eq{name_key}-fortigate".format(name_key=name_key)
        host_system_name = "qa-esx{name_key}.sun.corp.fortinet.com".format(name_key=name_key)
        return clone(template_vm_name, datastore_name, host_system_name, vm_names, basic_port)
    else:
        return do_action(vm_names, action_name)

if __name__ == '__main__':
    from minitest import *
    if '-v' in sys.argv or '--version' in sys.argv:
        print "current version: " + VERSION
        sys.exit(0)

    if len(sys.argv)==1:
        sys.argv.append('-h')
    parser = gen_parse()
    args = parser.parse_args()
    action_name = 'PowerOff'
    if args.action_name == 'clone':
        action_name = 'clone'
    elif args.action_name == 'delete':
        action_name = 'SafelyDestroy'
    elif args.action_name == 'poweron':
        action_name = 'PowerOn'
    elif args.action_name == 'poweroff':
        action_name = 'PowerOff'
    elif args.action_name == 'revert':
        action_name = 'RevertToCurrentSnapshot'
    template_vm_name = "FGT_VM64_5_2_0_GA_TEMPLATE-FMoM-QA"
    (args.thread_count, args.start_num, args.end_num, args.iteration_count, action_name, args.name_key, template_vm_name, args.basic_port).pp()
    end_num = args.end_num
    if end_num == -1:
        end_num = args.iteration_count * args.thread_count - 1
    else:
        if (end_num-args.start_num+1) % args.thread_count != 0:
            raise Exception("the vm count (end_num - start_num + 1 : {0}) cannot be divide by thead count!".format(str(end_num-args.start_num+1)))

    if args.vm_names == None:
        main(args.thread_count, args.start_num, end_num, action_name, args.name_key, 
                template_vm_name, args.basic_port)
    else:
        if args.action_name == 'clone' and args.basic_port <= 10000:
            print "please set basic_port larger than 10000!"
            sys.exit(10000)
        main_vm_names(action_name, args.name_key, args.vm_names, 
            template_vm_name, args.basic_port)

    # basic_port = 7000
    # python vmware_provision.py -n "107a" -a delete -t 1 -i 1
    # python vmware_provision.py -n "105a" -a clone -t 10 -i 50
    # python vmware_provision.py -n "106b" -a clone --vm_names SPECIAL_TEST_FGT_VM64_5_2_0 --basic_port 30000
    # 7d

    # with test(do_action):
    #     # vm_names = ['FGT_VM_107a_0000','FGT_VM_107a_0001']
    #     vm_names = ['FGT_VM_107a_0020']
    #     action_name = 'SafelyDestroy'
    #     # action_name = 'PowerOff'
    #     # action_name = 'PowerOn'

    #     do_action(vm_names, action_name)
    #     pass

    # with test(clone):
    #     # vm_names = ['FGT_VM_107a_0018','FGT_VM_107a_0019']
    #     vm_names = ['FGT_VM_107a_0020']
    #     name_key = "107a"
    #     template_vm_name = "FGT_VM64_5_2_0_GA_TEMPLATE-FMoM-QA"
    #     datastore_name = "eq{name_key}-fortigate".format(name_key=name_key)
    #     host_system_name = "qa-esx{name_key}.sun.corp.fortinet.com".format(name_key=name_key)
    #     basic_port = 7000
    #     clone(template_vm_name, datastore_name, host_system_name, vm_names, basic_port)

    #     pass

    # with test(main):
    #     name_key = "107a"
    #     # action_name = "SafelyDestroy"
    #     action_name = "clone"
    #     thread_count = 10
    #     iteration_count = 40
    #     # thread_count = 2
    #     # iteration_count = 2
    #     template_vm_name = "FGT_VM64_5_2_0_GA_TEMPLATE-FMoM-QA"
    #     basic_port = 7000
    #     main(thread_count, iteration_count, action_name, name_key, 
    #             template_vm_name, basic_port)

    # with test(generate_vm_names):
    #     thread_index, thread_count, start_num, end_num, name_key = (1,5, 0, 9, "107a")
    #     generate_vm_names(thread_index, thread_count, start_num, end_num, name_key).pp()
    #     # generate_vm_names(thread_index, thread_count, iteration_count, name_key).pp()
