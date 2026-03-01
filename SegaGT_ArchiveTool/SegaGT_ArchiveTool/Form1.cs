using SegaGT_ArchiveTool.Models;
using SegaGT_ArchiveTool.SEGAGTLib;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace SegaGT_ArchiveTool
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Shown(object sender, EventArgs e)
        {
            if (bgWorkerUnpack.IsBusy)
            {
                return;
            }

            string[] paths = Environment.GetCommandLineArgs();
            // not set files
            if (paths.Count() == 1)
            {
                return;
            } else if(paths.Count() > 2)
            {
                return;
            } else if (Path.GetExtension(paths[1]).ToLower() != ".exe")
            {
                return;
            }

            progressBar1.Minimum = 0;
            progressBar1.Value = 0;

            //string region = "EMPIRE";
            string region = "JP";

            // Get Values from Master Table
            TOC_Table tocTabl = new TOC_Table();
            DataRow[] dataRows = tocTabl.tocTable.Select($"region = '{region}'");
            DataRow row = dataRows[0];

            ArgsDoWorker argsDoWoker = new ArgsDoWorker();

            argsDoWoker.filePath = paths[1];
            argsDoWoker.fileDirectory = Path.GetDirectoryName(paths[1]);


            List<TOC_Entry> entrys = new List<TOC_Entry>();
            TOC_Entry str0 = (TOC_Entry)row[TOC_Table.COL_NAME_STR0];
            entrys.Add(str0);
            TOC_Entry str1 = (TOC_Entry)row[TOC_Table.COL_NAME_STR1];
            entrys.Add(str1);
            TOC_Entry str2 = (TOC_Entry)row[TOC_Table.COL_NAME_STR2];
            entrys.Add(str2);
            TOC_Entry str3 = (TOC_Entry)row[TOC_Table.COL_NAME_STR3];
            entrys.Add(str3);
            argsDoWoker.entrys = entrys;

            int totalFileCount = str0.count + str1.count + str2.count + str3.count;
            argsDoWoker.totalFileCount = totalFileCount;
            progressBar1.Maximum = totalFileCount;

            // Unpack
            bgWorkerUnpack.WorkerReportsProgress = true;
            bgWorkerUnpack.RunWorkerAsync(argsDoWoker);

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
            } else if (bytes.Length > 4 && bytes[0] == 'P' && bytes[1] == 'V' && bytes[2] == 'P' && bytes[3] == 'L')
            {
                return "pvp";
            }

            return "bin";

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
                if(adr > entry.size)
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

        private int Unpack(int idx, BackgroundWorker bgWorker, string filePath, string fileDirectory, List<TOC_Entry> entrys, UserStateProgressChanged argsProgressChanged, int progress)
        {
            string targetArcName = $"STR{idx}";
            string destDirectoryPath = $@"{fileDirectory}\extract\{targetArcName}";
            Directory.CreateDirectory(destDirectoryPath);
            int fileCount = entrys[idx].count;

            // EXE file of SsegGT
            using (FileStream exeFileStream = new FileStream(filePath, FileMode.Open, FileAccess.Read))
            // STRn(n=0~3) file
            using (FileStream arcFileStream = new FileStream($@"{fileDirectory}\{targetArcName}.BIN", FileMode.Open, FileAccess.Read))
            {
                exeFileStream.Seek(entrys[idx].adr, SeekOrigin.Begin);
                for (int i = 0; i < fileCount; i++)
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
                        UnpackMultiFile(i, destDirectoryPath, entry, arcFileStream);
                    }
                    else
                    {
                        // file
                        UnpackSingleFile(i, destDirectoryPath, entry, arcFileStream);
                    }

                    progress++;
                    bgWorker.ReportProgress(progress, argsProgressChanged); // update progress var
                }


            }

            return progress;
        }

        // Unpack
        private void bgWorkerUnpack_DoWork(object sender, DoWorkEventArgs e)
        {
            BackgroundWorker bgWorker = (BackgroundWorker)sender;
            ArgsDoWorker argments = e.Argument as ArgsDoWorker;
            string filePath = argments.filePath; // path of tbl file
            string fileDirectory = argments.fileDirectory;

            List<TOC_Entry> entrys = argments.entrys;

            int totalFileCount = entrys[0].count + entrys[1].count + entrys[2].count + entrys[3].count;

            UserStateProgressChanged argsProgressChanged = new UserStateProgressChanged();
            argsProgressChanged.maximum = totalFileCount;
            int progress = 0;

            try
            {
                progress = Unpack(0, bgWorker, filePath, fileDirectory, entrys, argsProgressChanged, progress);
                progress = Unpack(1, bgWorker, filePath, fileDirectory, entrys, argsProgressChanged, progress);
                progress = Unpack(2, bgWorker, filePath, fileDirectory, entrys, argsProgressChanged, progress);
                progress = Unpack(3, bgWorker, filePath, fileDirectory, entrys, argsProgressChanged, progress);

            }
            catch
            {
                bgWorker.ReportProgress(progress, argsProgressChanged);
                return;
            }

            MessageBox.Show("Success: Unpack Complete.");



        }

        // Unpackに関する表示の更新。
        private void bgWorkerUnpack_ProgressChanged(object sender, ProgressChangedEventArgs e)
        {
            //UserStateProgressChanged userState = e.UserState as UserStateProgressChanged;
            //progressBar1.Maximum = userState.maximum;

            progressBar1.Value = e.ProgressPercentage;
            label_prgoress_num.Text = $@"{e.ProgressPercentage.ToString()}/{ progressBar1.Maximum.ToString()}";

        }

        private void bgWorkerUnpack_RunWorkerCompleted(object sender, RunWorkerCompletedEventArgs e)
        {

        }
    }

}
