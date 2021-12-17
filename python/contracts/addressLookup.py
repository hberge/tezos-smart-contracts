import smartpy as sp

class AddressLookup(sp.Contract):
    """Contract to allow a global lookup register between Address and ID (nat).
    The use-case is to save on gas in contracts where addresses are frequently stored.

    Two cryptic error messages:
        UNKNOWN = The address or id is not registered.
        REREG   = The address or id has previously been registered and can't reregister.

    Notes: It may be useful for this contract to get a Michelson optimization to save on gas.        

    """
    def __init__(self, addr2id, id2addr, counter):
        """Initializes the contract. 
        
        Initialization is a bit fragile, could be improved, but used only at origination ...

        """

        # Define the contract storage data types for clarity
        self.init_type(sp.TRecord(
            addr2id=sp.TBigMap(sp.TAddress, sp.TNat),
            id2addr=sp.TBigMap(sp.TNat, sp.TAddress),
            counter=sp.TNat))

        self.init(addr2id=addr2id,id2addr=id2addr,counter=counter)

    @sp.onchain_view(name="has_addr")
    def view_has_addr(self,param):
        sp.result(self.data.addr2id.contains(param))

    @sp.onchain_view(name="has_sender")
    def view_has_sender(self):
        sp.result(self.data.addr2id.contains(sp.sender))

    @sp.onchain_view(name="get_counter")
    def view_get_counter(self):
        sp.result(self.data.counter)

    @sp.onchain_view(name="addr2id")
    def view_addr2id(self,param):
        sp.verify(self.data.addr2id.contains(param),message="UNKNOWN")
        sp.result(self.data.addr2id.get(param, default_value=None))

    @sp.onchain_view(name="id2addr")
    def view_id2addr(self,param):
        sp.verify(self.data.id2addr.contains(param),message="UNKNOWN")
        sp.result(self.data.id2addr.get(param, default_value=None))

    @sp.entry_point
    def register(self):
        """Register the sender. Fails if already known to avoid double spend."""
        sp.verify(~self.data.addr2id.contains(sp.sender),message="REREG")
        self.data.addr2id[sp.sender] = self.data.counter
        self.data.id2addr[self.data.counter] = sp.sender
        self.data.counter += 1

    @sp.entry_point
    def register_addr(self, param):
        """Register the address. Fails if already known to avoid double spend."""
        sp.set_type(param, sp.TAddress)
        sp.verify(~self.data.addr2id.contains(param),message="REREG")
        self.data.addr2id[param] = self.data.counter
        self.data.id2addr[self.data.counter] = param
        self.data.counter += 1

nulladdr = sp.address("tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU")
burnaddr = sp.address("tz1burnburnburnburnburnburnburjAYjjX")
acc1 = sp.test_account("account1")
acc2 = sp.test_account("account2")
acc3 = sp.test_account("account3")
addr2id = sp.big_map({nulladdr:0,burnaddr:1}, sp.TAddress, sp.TNat)
id2addr = sp.big_map({0:nulladdr,1:burnaddr}, sp.TNat, sp.TAddress)

@sp.add_test(name = "AddressLookup")
def test():
    scenario = sp.test_scenario()

    c1 = AddressLookup(addr2id, id2addr , 2)

    scenario += c1

    scenario += c1.register().run(valid=True,  sender=acc1)    
    scenario += c1.register().run(valid=True,  sender=acc2)
    scenario += c1.register().run(valid=False, sender=acc1)
    scenario += c1.register().run(valid=False, sender=acc2)
    scenario.verify(c1.view_addr2id(acc1.address)==2)
    scenario.verify(c1.view_id2addr(2)==acc1.address)
    scenario.verify(c1.view_addr2id(acc2.address)==3)
    scenario.verify(c1.view_id2addr(3)==acc2.address)
    scenario.verify(c1.view_get_counter()==4)
    scenario.verify(c1.view_has_addr(acc2.address)==True)
    scenario.verify(c1.view_has_addr(acc1.address)==True)
    scenario.verify(c1.view_has_addr(nulladdr)==True)
    scenario.verify(c1.view_has_addr(acc3.address)==False)

sp.add_compilation_target("address_lookup", AddressLookup(addr2id, id2addr , 2))
