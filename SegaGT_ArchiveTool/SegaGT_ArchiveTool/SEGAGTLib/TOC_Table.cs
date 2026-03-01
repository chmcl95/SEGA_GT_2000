using System.Data;

namespace SegaGT_ArchiveTool.SEGAGTLib
{
    class TOC_Entry
    {
        public int adr;
        public int count;
    }

    class TOC_Table
    {
        public DataTable tocTable;

        public const string TBL_NAME = "SEGAGT TOC Address";
        public const string COL_NAME_REGION = "region";
        public const string COL_NAME_STR0 = "tocSTR0";
        public const string COL_NAME_STR1 = "tocSTR1";
        public const string COL_NAME_STR2 = "tocSTR2";
        public const string COL_NAME_STR3 = "tocSTR3";

        public TOC_Table()
        {
            DataSet dataSet = new DataSet();
            tocTable = new DataTable(TBL_NAME);

            tocTable.Columns.Add(COL_NAME_REGION);
            DataColumn columnSTR0 = new DataColumn();
            columnSTR0.DataType = System.Type.GetType("SegaGT_ArchiveTool.SEGAGTLib.TOC_Entry");
            columnSTR0.ColumnName = COL_NAME_STR0;
            tocTable.Columns.Add(columnSTR0);
            DataColumn columnSTR1 = new DataColumn();
            columnSTR1.DataType = System.Type.GetType("SegaGT_ArchiveTool.SEGAGTLib.TOC_Entry");
            columnSTR1.ColumnName = COL_NAME_STR1;
            tocTable.Columns.Add(columnSTR1);
            DataColumn columnSTR2 = new DataColumn();
            columnSTR2.DataType = System.Type.GetType("SegaGT_ArchiveTool.SEGAGTLib.TOC_Entry");
            columnSTR2.ColumnName = COL_NAME_STR2;
            tocTable.Columns.Add(columnSTR2);
            DataColumn columnSTR3 = new DataColumn();
            columnSTR3.DataType = System.Type.GetType("SegaGT_ArchiveTool.SEGAGTLib.TOC_Entry");
            columnSTR3.ColumnName = COL_NAME_STR3;
            tocTable.Columns.Add(columnSTR3);
            dataSet.Tables.Add(tocTable);

            // Empire
            DataRow row = tocTable.NewRow();
            row[COL_NAME_REGION] = "EMPIRE";
            TOC_Entry str0 = new TOC_Entry();
            str0.adr = 0xDDDE8;
            str0.count = 1526;
            row[COL_NAME_STR0] = str0;
            TOC_Entry str1 = new TOC_Entry();
            str1.adr = 0xE0D98;
            str1.count = 275;
            row[COL_NAME_STR1] = str1;
            TOC_Entry str2 = new TOC_Entry();
            str2.adr = 0xE1630;
            str2.count = 247;
            row[COL_NAME_STR2] = str2;
            TOC_Entry str3 = new TOC_Entry();
            str3.adr = 0xE1DE8;
            str3.count = 41;
            row[COL_NAME_STR3] = str3;
            dataSet.Tables[TBL_NAME].Rows.Add(row);

            // JP
            row = tocTable.NewRow();
            row[COL_NAME_REGION] = "JP";
            str0 = new TOC_Entry();
            str0.adr = 0xDE8C0;
            str0.count = 1142;
            row[COL_NAME_STR0] = str0;
            str1 = new TOC_Entry();
            str1.adr = 0xE0C70;
            str1.count = 259;
            row[COL_NAME_STR1] = str1;
            str2 = new TOC_Entry();
            str2.adr = 0xE1488;
            str2.count = 241;
            row[COL_NAME_STR2] = str2;
            str3 = new TOC_Entry();
            str3.adr = 0xE1C10;
            str3.count = 41;
            row[COL_NAME_STR3] = str3;
            dataSet.Tables[TBL_NAME].Rows.Add(row);


        }
    }
}
