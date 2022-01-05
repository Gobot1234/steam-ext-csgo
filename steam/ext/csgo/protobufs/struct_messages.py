from steam.utils import StructIO
from ....protobufs.struct_messages import StructMessage


class NameItemRequest(StructMessage):
    name_tag_id: int
    item_id: int
    name: str

    def __bytes__(self) -> bytes:
        with StructIO() as io:
            io.write_u64(self.name_tag_id)
            io.write_u64(self.item_id)
            io.write(b"\x00" + self.name.encode("UTF-8") + b"\x00")
            return io.buffer


class DeleteItemRequest(StructMessage):
    item_id: int
