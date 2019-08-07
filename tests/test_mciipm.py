import io
import tempfile
import unittest

from cardutil.config import config
from cardutil.iso8583 import iso8583_to_dict
from cardutil.mciipm import block_1014, unblock_1014, VbsWriter, VbsReader, change_encoding, change_param_encoding, IpmReader, Unblock
from cardutil.outputter import dicts_to_csv

message_ebcdic_raw = (
        '1144'.encode('cp500') +
        b'\xF0\x10\x05\x42\x84\x61\x80\x02\x02\x00\x00\x04\x00\x00\x00\x00' +
        ('164444555544445555111111000000009999201508151715123456789012333123423579957991200000'
         '012306120612345612345657994211111111145BIG BOBS\\70 FERNDALE ST\\ANNERLEY\\4103  QLD'
         'AUS0080001001Y99901600000000000000011234567806999999').encode('cp500'))

message_ascii_raw = (
        b'1144' +
        b'\xF0\x10\x05\x42\x84\x61\x80\x02\x02\x00\x00\x04\x00\x00\x00\x00' +
        b'164444555544445555111111000000009999201508151715123456789012333123423579957991200000'
        b'012306120612345612345657994211111111145BIG BOBS\\70 FERNDALE ST\\ANNERLEY\\4103  QLD'
        b'AUS0080001001Y99901600000000000000011234567806999999')


class MciIpmTestCase(unittest.TestCase):
    def test_process_ebcdic_ipm_file(self):
        # add 5 records to a list
        message_list = [message_ebcdic_raw for _ in range(5)]

        # create the input ipm file bytes -- test_file
        with io.BytesIO() as vbs_in, io.BytesIO() as blocked_in, tempfile.TemporaryFile() as vbs_out, io.StringIO() as csv_out:
            # write vbs test file
            writer = VbsWriter(vbs_in)
            [writer.write(message) for message in message_list]
            writer.close()
            print_stream(vbs_in, "VBS in data")

            # write 1014 test file
            block_1014(vbs_in, blocked_in)
            print_stream(blocked_in, "Blocked in data")

            # unblock test file
            unblock_1014(blocked_in, vbs_out)
            print_stream(vbs_out, "VBS out data")

            # get vbs record reader
            vbs_iter = VbsReader(vbs_out)
            out_list = (iso8583_to_dict(record, config["bit_config"], "cp500") for record in vbs_iter)
            print(list(out_list))
            out_list = IpmReader(Unblock(blocked_in), encoding='cp500')
            print(list(out_list))
            out_list.vbs_data.seek(0)
            out_list.vbs_data.buffer = b''
            dicts_to_csv(out_list, config['output_data_elements'], csv_out)
            print_stream(csv_out, "CSV data")

            # get vbs record reader
            vbs_iter = VbsReader(vbs_in)
            out_list = (iso8583_to_dict(record, config["bit_config"], "cp500") for record in vbs_iter)
            dicts_to_csv(out_list, config['output_data_elements'], csv_out)
            print_stream(csv_out, "CSV data")

    def test_change_encoding(self):
        # add 5 records to a list
        message_list = [message_ebcdic_raw for _ in range(5)]

        # create the input ipm file bytes -- test_file
        with io.BytesIO() as vbs_in, io.BytesIO() as blocked_in, tempfile.TemporaryFile() as flipped_out1, tempfile.TemporaryFile() as flipped_out2:
            # write vbs test file
            writer = VbsWriter(vbs_in)
            [writer.write(message) for message in message_list]
            writer.close()
            print_stream(vbs_in, "VBS in data")

            # write 1014 test file
            block_1014(vbs_in, blocked_in)
            print_stream(blocked_in, "Blocked in data")

            change_param_encoding(blocked_in, flipped_out1)
            print_stream(flipped_out1, "Flipped out 1")

            blocked_in.seek(0)
            change_encoding(blocked_in, flipped_out2)
            print_stream(flipped_out1, "Flipped out 2")


def print_stream(stream, description):
    stream.seek(0)
    data = stream.read()
    print(description)
    print(data)
    stream.seek(0)


if __name__ == '__main__':
    unittest.main()
