using System;
using System.IO;

namespace SegaGT2000Tool.SEGAGTLib
{
    class Entry
    {
        public int offset;
        public int size;

        /// <summary>
        /// 
        /// </summary>
        /// <param name="fileStream"></param>
        /// <returns>false:Success</returns>
        public bool Unpack(FileStream fileStream)
        {
            byte[] bytes = new byte[4];
            fileStream.Read(bytes, 0x00, bytes.Length);
            offset = BitConverter.ToInt32(bytes, 0x00);
            fileStream.Read(bytes, 0x00, bytes.Length);
            size = BitConverter.ToInt32(bytes, 0x00);

            return false;
        }
    }
}
