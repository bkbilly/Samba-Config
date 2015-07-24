import inspect
from gi.repository import GObject,Gtk
from xml.etree.cElementTree import ElementTree


class builder():
    def __init__(self,filename,window):
        self.widgets = {}
        self.widgets = {}
        self.builder = Gtk.Builder()
        self.builder.add_from_file(filename)
        
        self.ShowWindow(window)
        
        tree = ElementTree()
        tree.parse(filename)
        
        ele_widgets = tree.getiterator("object")
        for ele_widget in ele_widgets:
            name = ele_widget.attrib['id']
            widget = self.builder.get_object(name)

            self.widgets[name] = widget

    def ShowWindow(self,window):
        self.builder.get_object(window).show()
    
    def get_ui(self, callback_obj):
        '''Return the attributes of the widgets and Connects to Handler'''
        #Get all methods of class window and write them to a dictionary 
        methods = []
        for k in dir(callback_obj):
            try:
                attr = getattr(callback_obj, k)
            except:
                continue
            if inspect.ismethod(attr):
                methods.append((k, attr))
        methods.sort()
        dict_methods = dict(methods)
        callback_handler_dict = {}
        callback_handler_dict.update(dict_methods)


        for (widget_name, widget) in self.widgets.items():
            setattr(self, widget_name, widget) #Return the attribute
            signal_names = self.__get_signals(widget) #Get a list of the widget signals

            for signal_name in signal_names:
                signal_name = signal_name.replace("-", "_")
                handler_names = ["on_%s_%s" % (widget_name, signal_name)]
                
                #For every method of the window, connect the signals
                for handler_name in handler_names:
                    target = handler_name in callback_handler_dict.keys()
                    if target:
                        widget.connect(signal_name, callback_handler_dict[handler_name])

        return self


    def __get_signals(self, widget):
        '''Return the signals of the widget'''
        signal_ids = []
        try:
            widget_type = type(widget)
            while widget_type:
                signal_ids.extend(GObject.signal_list_ids(widget_type))
                widget_type = GObject.type_parent(widget_type)
        except RuntimeError:
            pass
        signal_names = [GObject.signal_name(sid) for sid in signal_ids]
        return signal_names
