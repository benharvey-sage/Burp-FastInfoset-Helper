using System;
using System.IO;
using System.Text;
using System.Xml;
using System.IO.Compression;
using LiquidTechnologies.FastInfoset;

namespace FastInfosetHelper
{
    class Program
    {
        static byte[] gunzip(byte[] compressedBytes)
        {
            MemoryStream compressedStream = new MemoryStream(compressedBytes);
            MemoryStream decompressedStream = new MemoryStream();
            using (var decompressor = new GZipStream(compressedStream, CompressionMode.Decompress))
            {
                decompressor.CopyTo(decompressedStream);
            }

            return decompressedStream.ToArray();
        }
        static byte[] Decode(string base64FastInfosetData)
        {
            // Convert the base64 string to a byte array and decompress if required
            byte[] fastInfosetBytes = Convert.FromBase64String(base64FastInfosetData);
            if (fastInfosetBytes[0] == '\x1F' && fastInfosetBytes[1] == '\x8B')
            {
                fastInfosetBytes = gunzip(fastInfosetBytes);
            }

            // Use a MemoryStream to hold the byte array
            var encodedStream = new MemoryStream(fastInfosetBytes);

            // Step 1: Create a MemoryStream to hold the XML data
            using (MemoryStream decodedStream = new MemoryStream())
            {
                // Step 2: Create an XmlWriter to write to the MemoryStream
                using (XmlWriter xmlWriter = XmlWriter.Create(decodedStream, new XmlWriterSettings { Indent = true, Encoding = Encoding.UTF8 }))
                {
                    // Step 3: Create an XmlReader to read from the XML string
                    using (var xmlReader = XmlReader.Create(new FIReader(encodedStream), null))
                    {

                        // Step 4: Write the nodes using WriteNode
                        xmlWriter.WriteNode(xmlReader, true);
                    }
                }
                byte[] xmlBytes = decodedStream.ToArray();
                return xmlBytes;
            }
        }

        static byte[] Encode(string base64XmlString)
        {

            // Convert the base64 string to a byte array
            byte[] xmlStringBytes = Convert.FromBase64String(base64XmlString);

            // Convert the base64 into the XML string
            string xmlString = Encoding.UTF8.GetString(xmlStringBytes);

            // Step 1: Convert the XML string back into Fast Infoset data
            using (MemoryStream fastInfosetStream = new MemoryStream())
            {
                // Step 2: Create an XmlReader to read the XML string
                using (var xmlReader = XmlReader.Create(new StringReader(xmlString)))
                {
                    // Step 3: Create a FastInfosetWriter to write to the MemoryStream
                    using (var fiWriter = XmlWriter.Create(new FIWriter(fastInfosetStream)))
                    {
                        // Step 4: Write the XML nodes into Fast Infoset format
                        XmlDocument xmlDoc = new XmlDocument();
                        xmlDoc.Load(xmlReader);
                        xmlDoc.WriteTo(fiWriter);
                        fiWriter.Close();
                    }
                }
                byte[] fastInfosetBytes = fastInfosetStream.ToArray();
                return fastInfosetBytes;
            }
        }

        static void OutputResult(byte[] data)
        {
            string result = "";
            // UTF-8 BOM (EF BB BF)
            byte[] utf8Bom = new byte[] { 0xEF, 0xBB, 0xBF };

            // Check if the byte array starts with the UTF-8 BOM
            if (
                data[0] == utf8Bom[0] &&
                data[1] == utf8Bom[1] &&
                data[2] == utf8Bom[2])
            {
                // Create a new array excluding the BOM
                byte[] byteArrayWithoutBom = new byte[data.Length - 3];
                Array.Copy(data, 3, byteArrayWithoutBom, 0, byteArrayWithoutBom.Length);
                result = Convert.ToBase64String(byteArrayWithoutBom);
            }
            else
            {
                // No BOM, so keep as is
                result = Convert.ToBase64String(data);
            }
            Console.Write(result);
        }
        static void Main(string[] args)
        {
            if (args.Length < 2)
            {
                Console.Write("[X] Error. Args must be [encode/decode] followed by a base64 string to encode/deocde.");
                Environment.Exit(1);
            }

            string method = args[0];
            string base64data = args[1];

            switch (method.ToLower())
            {
                case "encode":
                    OutputResult(Encode(base64data));
                    break;
                case "decode":
                    OutputResult(Decode(base64data));
                    break;
                default:
                    Console.Write("[X] Error. Args must be [encode/decode] followed by a base64 string to encode/deocde.");
                    Environment.Exit(1);
                    break;
            }
        }
    }
}
