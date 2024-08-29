from burp import IBurpExtender
from burp import IMessageEditorTabFactory
from burp import IMessageEditorTab
from base64 import b64encode, b64decode
import subprocess
import array

# java imports
from java.util import ArrayList

# Add your EXE path here
FASTINFOSETHELPER_EXE_PATH = "C:\\Path\\To\\The\\Helper.exe"

class BurpExtender(IBurpExtender, IMessageEditorTabFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("FastInfoset Helper")
        callbacks.registerMessageEditorTabFactory(self)
        
    def createNewInstance(self, controller, editable):
        # Return a new instance of our custom tab
        return FastInfosetDecoderTab(self, controller, editable)
    
    print ("[*] FastInfoset Helper ready!")
                    
class FastInfosetDecoderTab(IMessageEditorTab):
    def __init__(self, extender, controller, editable):
        self._extender = extender
        self._helpers = extender._helpers
        self._controller = controller
        self._editable = editable
        
        # Create a text editor to display the decoded content
        self._txtInput = self._extender._callbacks.createTextEditor()
        self._txtInput.setEditable(editable)
        
        # Keep track of changes
        self._isModified = False
        self._initialContent = None
        self._currentContent = None
        self._httpMessage = None
                
    def getTabCaption(self):
        # Name of the custom tab
        return "FastInfoset Helper"
        
    def getUiComponent(self):
        return self._txtInput.getComponent()
        
    def isEnabled(self, content, isRequest):
        if content is None:
            return False
        
        if isRequest:
            analyzedMessage = self._helpers.analyzeRequest(content)
        else:
            analyzedMessage = self._helpers.analyzeResponse(content)
        
        headers = list(analyzedMessage.getHeaders())
        if 'content-type: application/fastinfoset' in [str(header).lower() for header in headers]:
           return True
        else:
            return False
            
    def getMessage(self):
        if self._isModified:
            # If the content has been modified, return the modified message
            modified_body = self._currentContent

            analyzedMessage = self._helpers.analyzeRequest(self._httpMessage)
            headers = analyzedMessage.getHeaders()
            
            # Convert the headers to a java.util.List
            java_headers = ArrayList()
            for header in headers:
                java_headers.add(header)
            
            # Rebuild the message. It'll be still be in XML at this point
            message = self._helpers.buildHttpMessage(java_headers, modified_body)
            # Encode the XML to FastInfoset, then rebuild the message again
            modified_body = array.array('b',self.encodeFastInfoset(isRequest=True, data=message))
            message = self._helpers.buildHttpMessage(java_headers, modified_body)
            return message
        
        return self._currentMessage

    def isModified(self):
        self._currentContent = self._txtInput.getText()

        if self._currentContent != self._initialContent and self._initialContent != None:
            self._isModified = True
            return self._isModified
        else:
            self._isModified = False
            return self._isModified

    def getSelectedData(self):
        # Return the selected text in the custom tab (if needed)
        return self._txtInput.getSelectedText()
    
    def setMessage(self, content, isRequest):
        self._isModified = False  # Reset modification flag

        if content is None:
            self._txtInput.setText(None)
        else:
            self._httpMessage = content
            decoded_body = array.array('b',self.decodeFastInfoset(isRequest, content).encode('utf-8'))
            # Set the decoded content in the text editor
            self._txtInput.setText(decoded_body)
            # Store the initial content
            self._initialContent = decoded_body

    def runDecoderEncoderTool(self, method, body):
        b64body = b64encode(body)

        try:
            # Run the tools and capture the output
            process = subprocess.Popen([FASTINFOSETHELPER_EXE_PATH, method, b64body], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
    
            # Decode the output from bytes to string    
            output = output.decode('utf-8').strip()
            error = error.decode('utf-8').strip()
    
            if process.returncode == 0:
                return b64decode(output)
            else:
                print("[X] {} failed with return code {}".format(method, process.returncode))
                print("[X] Error:\n", error)
    
        except Exception as e:
            print("[X] An error occurred while running the EXE:", str(e))

    def getBody(self, isRequest, data):
        if isRequest:
            info = self._helpers.analyzeRequest(data)
        else:
            info = self._helpers.analyzeResponse(data)
        
        bodyOffset = info.getBodyOffset()
        body = data[bodyOffset:]

        return body

    def decodeFastInfoset(self, isRequest, data):
        body = self.getBody(isRequest, data)
        decodedBytes = self.runDecoderEncoderTool("decode", body)

        return decodedBytes
        
        
    def encodeFastInfoset(self, isRequest, data):
        body = self.getBody(isRequest, data)
        encodedBytes = self.runDecoderEncoderTool("encode", body)

        return encodedBytes
