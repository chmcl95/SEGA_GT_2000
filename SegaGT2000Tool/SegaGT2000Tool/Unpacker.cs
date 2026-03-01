using SegaGT2000Tool.SEGAGTLib;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SegaGT2000Tool
{
    class Unpacker
    {
        private string _exePath;
        private string _inputPath;
        private string _destPath;

        private TOCInformation _toc;

        public Unpacker(string revision, string exePath, string inputPath, string outputPath)
        {
            _exePath = exePath;
            _inputPath = inputPath;
            _destPath = outputPath;

            if (!TableOfContents.TOCInfos.TryGetValue(revision, out TOCInformation toc))
            {
                throw new ArgumentException("Invalid or non-supported exe of Sega GT provided.");
            }

            _toc = toc;
        }

        public void Unpack()
        {
            Console.WriteLine("Starting to unpack...");

            Directory.CreateDirectory(_destPath);

            TOC_Entry strNInfo = _toc.str3;



            // exe file
            using (FileStream exeFileStream = new FileStream(_exePath, FileMode.Open, FileAccess.Read))
            // arc file
            using (FileStream arcFileStream = new FileStream(_inputPath, FileMode.Open, FileAccess.Read))
            {
                exeFileStream.Seek(strNInfo.adr, SeekOrigin.Begin);
                for (int i = 0; i < strNInfo.count; i++)
                {
                    Entry entry = new Entry();
                    entry.Unpack(exeFileStream);
                    if (i > 0 && entry.offset < 1)
                    {
                        exeFileStream.Seek(-8, SeekOrigin.Current);
                        break;
                    }

                    byte[] bytes = new byte[4];
                    arcFileStream.Seek(entry.offset, SeekOrigin.Begin);
                    arcFileStream.Read(bytes, 0x00, 4);
                    int first4Byte = BitConverter.ToInt32(bytes, 0);

                    if (first4Byte > 0x00 && first4Byte < 0xFFFF)
                    {
                        // container
                        UnpackMultiFile(i, _destPath, entry, arcFileStream);
                    }
                    else
                    {
                        // file
                        UnpackSingleFile(i, _destPath, entry, arcFileStream);
                    }
                }
            }

            Console.WriteLine("Done.");
            return;
        }
        private void UnpackMultiFile(int idx, string destDirectoryPathBase, Entry entry, FileStream arcFileStream)
        {
            string destDirectoryPath = $@"{destDirectoryPathBase}\{string.Format("{0:D8}", idx)}";
            Directory.CreateDirectory(destDirectoryPath);
            byte[] bytes = new byte[4];
            arcFileStream.Seek(entry.offset, SeekOrigin.Begin);

            arcFileStream.Read(bytes, 0x00, 4);
            uint count = BitConverter.ToUInt32(bytes, 0);
            List<int> adrList = new List<int>();
            for (int i = 0; i < count; i++)
            {
                arcFileStream.Read(bytes, 0x00, 4);
                int adr = BitConverter.ToInt32(bytes, 0);
                adrList.Add(adr);
            }

            foreach (int adr in adrList)
            {
                if (adr > entry.size)
                {
                    // force change to single file
                    UnpackSingleFile(idx, destDirectoryPathBase, entry, arcFileStream);
                    Directory.Delete(destDirectoryPath, true);
                    return;
                }
            }

            for (int i = 0; i < count; i++)
            {
                int nextAdr = i < count - 1 ? adrList[i + 1] : entry.size;
                int size = nextAdr - adrList[i];
                byte[] destBytes = new byte[size];
                arcFileStream.Read(destBytes, 0x00, size);
                string extension = DetectExtension(destBytes);
                string destFileName = string.Format("{0:D8}.{1}", i, extension);
                string fullpath = $@"{destDirectoryPath}\{destFileName}";
                using (FileStream destFileStream = new FileStream(fullpath, FileMode.Create, FileAccess.Write))
                {
                    destFileStream.Write(destBytes, 0x00, size);
                }
            }

            return;
        }

        private void UnpackSingleFile(int idx, string destDirectoryPath, Entry entry, FileStream arcFileStream)
        {
            byte[] destBytes = new byte[entry.size];
            arcFileStream.Seek(entry.offset, SeekOrigin.Begin);
            arcFileStream.Read(destBytes, 0x00, entry.size);

            string extension = DetectExtension(destBytes);

            string destFileName = string.Format("{0:D8}.{1}", idx, extension);
            string fullpath = $@"{destDirectoryPath}\{destFileName}";
            using (FileStream destFileStream = new FileStream(fullpath, FileMode.Create, FileAccess.Write))
            {
                destFileStream.Write(destBytes, 0x00, entry.size);
            }

            return;
        }
        private string DetectExtension(byte[] bytes)
        {
            if (bytes.Length > 2 && bytes[0] == 'N' && bytes[1] == 'J')
            {
                // NJ file
                return "nj";
            }
            else if (bytes.Length > 4 && bytes[0] == 'G' && bytes[1] == 'B' && bytes[2] == 'I' && bytes[3] == 'X')
            {
                return "pvr";
            }
            else if (bytes.Length > 4 && bytes[0] == 'P' && bytes[1] == 'V' && bytes[2] == 'P' && bytes[3] == 'L')
            {
                return "pvp";
            }

            return "bin";

        }

    }
}
