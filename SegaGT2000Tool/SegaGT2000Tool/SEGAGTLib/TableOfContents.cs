using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SegaGT2000Tool.SEGAGTLib
{
    public class TOC_Entry
    {
        public TOC_Entry(int adr, int count)
        {
            this.adr = adr;
            this.count = count;
        }

        public int adr { get; }
        public int count { get; }
    }
    // str0: car model, texture
    // str1: track model, texture
    // str2: menu model, texture
    // str3: ?
    partial record TOCInformation(TOC_Entry[] STRn);

    class TableOfContents
    {
        public static Dictionary<string, TOCInformation> TOCInfos = new()
        {
            { "EMPIRE"  , new TOCInformation(new TOC_Entry[4]{ new TOC_Entry(0xDDDE8, 1526), new TOC_Entry(0xE0D98, 275), new TOC_Entry(0xE1630, 247), new TOC_Entry(0xE1DE8, 41) }) },
            { "PCJP"    , new TOCInformation(new TOC_Entry[4]{ new TOC_Entry(0xDE8C0, 1142), new TOC_Entry(0xE0C70, 259), new TOC_Entry(0xE1488, 241), new TOC_Entry(0xE1C10, 41) }) },
            { "DCPROTO" , new TOCInformation(new TOC_Entry[4]{ new TOC_Entry(0xDC5A8, 1161), new TOC_Entry(0xDE9F0, 261), new TOC_Entry(0xDF218, 241), new TOC_Entry(0xDF9A0, 41) }) }
        };
    }

}
