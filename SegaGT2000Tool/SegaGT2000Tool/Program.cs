using CommandLine;
using System;
using System.IO;

namespace SegaGT2000Tool
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("SegaGT2000 Tool - by chmcl95");
            Console.WriteLine();

            Parser.Default.ParseArguments<UnpackVerbs, PatchVerbs>(args)
                .WithParsed<UnpackVerbs>(Unpack)
                .WithParsed<PatchVerbs>(Patch);
        }

        public static void Unpack(UnpackVerbs options)
        {
            if (!File.Exists(options.ExePath))
            {
                Console.WriteLine($"Provided EXE file '{options.ExePath}' does not exist.");
                return;
            }

            if (!File.Exists(options.InputPath))
            {
                Console.WriteLine($"Provided STR0.BIN or STR1.BIN or STR2.BIN or STR3.BIN '{options.InputPath}' does not exist.");
                return;
            }
            string outputPath = options.OutputPath;
            if (string.IsNullOrEmpty(options.OutputPath))
            {
                outputPath = $"{Path.GetDirectoryName(options.InputPath)}\\extracted";
            }

            Unpacker unpacker = new Unpacker(options.Revision,  options.ExePath, options.InputPath, outputPath);
            unpacker.Unpack();

            return;
        }

        public static void Patch(PatchVerbs options)
        {
            if (!File.Exists(options.ExePath))
            {
                Console.WriteLine($"Provided EXE file '{options.ExePath}' does not exist.");
                return;
            }

            if (!Directory.Exists(options.InputPath))
            {
                Console.WriteLine($"Provided STR0.BIN or STR1.BIN or STR2.BIN or STR3.BIN '{options.InputPath}' does not exist.");
                return;
            }

            string outputPath = options.OutputPath;
            if (string.IsNullOrEmpty(options.OutputPath))
            {
                outputPath = $"{Path.GetDirectoryName(options.ExePath)}\\patched";
            }

            //Pactcher patcher = new Pactcher(options.ElfPath, options.InputPath, outputPath);
            //patcher.Patch();

            return;
        }
    }


    [Verb("unpack", HelpText = "Unpacks STRn.BIN  Files are extract in \"extracted\" folder.(Deafult)")]
    public class UnpackVerbs
    {
        [Option('r', "rev", Required = true, HelpText = "Revision. like EMPIRE")]
        public string Revision { get; set; }

        [Option('i', "input", Required = true, HelpText = "Input .BIN file like STR1.BIN")]
        public string InputPath { get; set; }

        [Option('e', "exe-path", Required = true, HelpText = "Input exe file. Example: SegaGT.EXE")]
        public string ExePath { get; set; }

        [Option('o', "output", Required = false, HelpText = "Output directory for the extracted files.")]
        public string OutputPath { get; set; }

    }

    [Verb("patch", HelpText = "Packs . Also patching elf file. Files are generat in \"patched\" folder.(Deafult)")]
    public class PatchVerbs
    {
        [Option('i', "input", Required = true, HelpText = "Input Directry. Need extracted STRn.BIN files.")]
        public string InputPath { get; set; }

        [Option('e', "exe-path", Required = true, HelpText = "Input exe file. Example: SegaGT.EXE")]
        public string ExePath { get; set; }

        [Option('o', "output", Required = false, HelpText = "Output directory for the patched files.")]
        public string OutputPath { get; set; }

    }
}
