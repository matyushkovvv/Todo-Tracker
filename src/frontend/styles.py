DIALOG_STYLE = """
    QDialog {
        background: transparent;
    }
    
    #mainContainer {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                   stop:0 #667eea, stop:1 #764ba2);
        border-radius: 20px;
        padding: 40px;
        color: white;
    }
    
    #titleLabel {
        font-size: 28px;
        font-weight: bold;
        color: white;
        margin-bottom: 30px;
    }
    
    #nameInput {
        background: rgba(255, 255, 255, 0.2);
        border: 2px solid rgba(255, 255, 255, 0.4);
        border-radius: 10px;
        padding: 15px;
        font-size: 16px;
        color: white;
        margin-bottom: 20px;
    }
    
    #nameInput::placeholder {
        color: rgba(255, 255, 255, 0.7);
    }
    
    #submitButton {
        background: white;
        color: #764ba2;
        border-radius: 10px;
        padding: 12px;
        font-size: 16px;
        font-weight: bold;
        border: none;
        min-width: 120px;
    }
    
    #submitButton:hover {
        background: rgba(255, 255, 255, 0.9);
    }
    
    #submitButton:pressed {
        background: rgba(255, 255, 255, 0.8);
    }
"""