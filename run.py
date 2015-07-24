#Packeges needed: samba
from gi.repository import Gtk
from subprocess import Popen, PIPE
import os

from builder import builder

class WinFunc():
    '''Functions Class'''
    def Initialize(self,ROOTPASS):
        '''Define Variables and Call Methods for initialization'''
        #DEFINE Variables
        self.SMBFILE="/etc/samba/smb.conf"
        self.ROOTPASS=ROOTPASS+"\n"
        self.NOPASS="No Password"
        self.HIDEPASS="*******"
        self.SMBLIST=[]
        self.SharesList=[]

        #CALL Methods
        self.__CreateSMBLIST()
        self.__CreateSharesList()
        self.__WriteUsers()
        self.__WriteConfig()
        self.ui.NetbiosName_Entry.set_text(self.__GetProperties("netbios"))
        self.ui.Workgroup_Name.set_text(self.__GetProperties("workgroup"))
        self.ui.AllowPassword_Switch.set_active(self.__GetProperties("null passwords"))
        self.ui.SharePrinters_Switch.set_active(self.__PrintShareExists())

#Files-Lists
    def __CreateSMBLIST(self):
        '''Private Method to READ the smb config file and write to SMBLIST with the proper names'''
        f = open(self.SMBFILE,"r")
        for line in f:
            if (line.replace(" ","")!="\n"):
                line=line.strip()
                if (line.find("#")!=0 and line.find(";")!=0):
                    if(line[0]=="["):
                        templist=[]
                        self.SMBLIST.append(templist)
                    templist.append(line.lower())
        f.close()
        self.__FixSynonyms()

    def __FixSynonyms(self):
        '''Fix the names in the SMBLIST'''
        for title in self.SMBLIST:
            for item in title:
                titleID=self.SMBLIST.index(title)
                itemID=title.index(item)
                if(item.find("browseable")==0):
                    self.SMBLIST[titleID][itemID] = item.replace("browseable","browsable")
                elif(item.find("create mode")==0):
                    self.SMBLIST[titleID][itemID] = item.replace("create mode","create mask")
                elif(item.find("directory mode")==0):
                    self.SMBLIST[titleID][itemID] = item.replace("directory mode","directory mask")
                elif(item.find("guest ok")==0):
                    self.SMBLIST[titleID][itemID] = item.replace("guest ok","public")
                elif(item.find("directory")==0):
                    self.SMBLIST[titleID][itemID] = item.replace("directory","path")
                elif(item.find("print ok")==0):
                    self.SMBLIST[titleID][itemID] = item.replace("print ok","printable")
                elif(item.find("write ok")==0):
                    self.SMBLIST[titleID][itemID] = item.replace("write ok","read only")
                elif(item.find("writeable")==0 or item.find("writable")==0):
                    invert = item.split('= ')[1]
                    if (invert == "no"):
                        self.SMBLIST[titleID][itemID] = "read only = yes"
                    elif (invert == "yes"):
                        self.SMBLIST[titleID][itemID] = "read only = no"

    def __CreateSharesList(self):
        ''' Search in the SMBLIST for shares and create a new list, SharesList, to store them '''
        for title in self.SMBLIST:
            if (title[0].find("[global]")!=0 and title[0].find("[print")!=0):
                ShareName=""
                Directory=""
                Permissions="Writable"
                Comment=""
                Access="User Access"
                ShareName=title[0][1:-1]
                for item in title:
                    if(item.find("path")==0):
                        Directory=item.split('= ')[1]
                    elif(item.find("comment")==0):
                        Comment=item.split('= ')[1]
                    elif(item.find("public")==0):
                        if(item.split('= ')[1]=="yes"):
                            Access="public"
                    elif(item.find("valid users")==0):
                        Access=item.split("= ")[1]
                    elif(item.find("read only")==0):
                        if(item.split('= ')[1]=="yes"):
                            Permissions="Read Only"


                #Append items in List
                self.SharesList.append([ShareName,Directory,Comment,Access,Permissions])
                print self.SharesList

    def __WriteConfig(self):
        ''' Write the whole smb config file in the Configuration Tab of the application GUI'''
        self.ui.ShowConfig_textview.get_buffer().set_text("")
        f = open(self.SMBFILE,"r")
        for line in f:
            self.ui.ShowConfig_textview.get_buffer().\
            insert(self.ui.ShowConfig_textview.get_buffer().get_end_iter(), line)
        f.close()

#Settings Tab
    def __GetProperties(self,search):
        ''' Search in the SMBLIST to for specific configuration '''
        for title in self.SMBLIST:
            for item in title:
                if(search.find('[')==0):
                    if(item==search):
                        return item
                elif(item.find(search)==0):
                    item = item.split('= ')[1]
                    if (item=="true" or item=="yes"):
                        return True
                    elif (item=="false" or item=="no"):
                        return False
                    else:
                        return item
        return "Not Found"

    def __PrintShareExists(self):
        ''' Search the SMBLIST for printer share '''
        if (self.__GetProperties("printing")=="cups" and
            self.__GetProperties("printcap name")=="cups" and
            self.__GetProperties("[print$]")== "[print$]" and
            self.__GetProperties("[printers]") == "[printers]"):
            return True
        else:
            return False

#Shares Tab
    def WriteShares(self):
        ''' Write all the shares from the SharesList to Shares Tab in the application GUI '''
        self.ui.SharesListStore.clear()
        for share in self.SharesList:
            self.ui.SharesListStore.append([share[0],share[1],share[3]+"/"+share[4]])

    def DeleteShares(self):
        ''' Get the selected row and delete it from Shares Tab and from SharesList '''
        (model,paths)=self.ui.SharesTree.get_selection().get_selected_rows()
        iter = model.get_iter(paths[0])
        ShareName = model.get_value(iter,0)

        for share in self.SharesList:
            if(share[0]==ShareName):
                break

        self.SharesList.remove(share)
        model.remove(iter)

    def AddShares(self):
        ''' Open new empty Window for share '''
        self.__OpenShares("","","","","","Add Shares")

    def EditShares(self):
        ''' Get the selected share and open a new share Window based on the SharesList '''
        (model,paths)=self.ui.SharesTree.get_selection().get_selected_rows()
        iter = model.get_iter(paths[0])

        ShareName = model.get_value(iter,0)
        for share in self.SharesList:
            if(share[0]==ShareName):
                break
        self.__OpenShares(share[0],share[1],share[2],share[3],share[4],"Edit "+ShareName)

    def __OpenShares(self, Name,Directory,Description,Access,Permissions,Title):
        ''' Write the properties to the Shares Window '''
        self.ui.TabsNotebook.set_current_page(0)
        self.ui.ShareOptions.set_title(Title)
        self.ui.SharesEntryName.set_text(Name)
        self.ui.SharesEntryDirectory.set_text(Directory)
        self.ui.SharesEntryDescription.set_text(Description)
        if(Access=="public" or Access==""):
            self.ui.SharesCheckPublic.set_active(True)
        else:
            print Access
            self.ui.SharesCheckPublic.set_active(False)
        if(Permissions=="Read Only"):
            self.ui.SharesCheckWritable.set_active(False)
        else:
            self.ui.SharesCheckWritable.set_active(True)

        self.MainWindow.ShowWindow("ShareOptions")

    def ConfirmShareChanges(self):
        #Get Options from the window
        Title = self.ui.ShareOptions.get_title()
        ShareName = self.ui.SharesEntryName.get_text()
        Directory = self.ui.SharesEntryDirectory.get_text()
        Description = self.ui.SharesEntryDescription.get_text()
        if(self.ui.SharesCheckPublic.get_active()==True):
            Access="public"
        else:
            Access="User Access"
        if(self.ui.SharesCheckWritable.get_active()==True):
            Permissions="Writable"
        else:
            Permissions="Read Only"

        #Get Selected Users who have access to the shared directory
        if (Access != "public"):
            Users = ""
            (model,paths)=self.ui.ShareUsers.get_selection().get_selected_rows()
            paths.reverse()
            for rowIter in paths:
                iter = model.get_iter(rowIter)
                Users = Users + " " + model.get_value(iter,0)
            Access = Users

        #Check if Everything is Fine
        if(ShareName=="" or Directory=="" or Access==""):
            print "Missing !!!!"
            return False
        for share in self.SharesList:
            if (share[0]==ShareName and Title.split()[0]=="Add"):
                print "Already in List"
                return False
            if not os.path.exists(Directory):
                print "File Path Doesn't Exist"
                return False

        #Update the SharesList with the new Options
        if(Title.split()[0]=="Add"):
            self.SharesList.append([ShareName,Directory,Description,Access,Permissions])
            print self.SharesList
            self.ui.ShareOptions.hide()
        else:
            i=0
            for share in self.SharesList:
                if(share[0]==Title.split()[1]):
                    break
                i+=1
            self.SharesList[i]=[ShareName,Directory,Description,Access,Permissions]
            self.ui.ShareOptions.hide()

#Users Tab
    def __WriteUsers(self):
        ''' Write all the Users from the the output of the pdbedit to Users Tab in the application GUI '''
        self.ui.UsersListStore.clear()
        UserName = Popen("sudo -S pdbedit -Lw".split(), stdout=PIPE, stdin=PIPE).communicate(self.ROOTPASS)[0]
        if (len(UserName)>0):
            UserName=UserName.strip().split("\n")
            for item in UserName:
                if(item.find("WARNING")<0):
                    if(item.find("NO PASSWORD")>=0):
                        UsesPass=self.NOPASS
                    else:
                        UsesPass=self.HIDEPASS
                    UserName=item[:item.find(":")]
                    self.ui.UsersListStore.append([UserName,UsesPass])

    def DeleteUser(self):
        ''' Delete the selected User from the application GUI and from the system '''
        (model,paths)=self.ui.UsersTree.get_selection().get_selected_rows()
        paths.reverse()
        iter = model.get_iter(paths[0])
        User = model.get_value(iter,0)
        output = Popen(("sudo -S smbpasswd -x " + User).split(), stdin=PIPE, stdout=PIPE).communicate(self.ROOTPASS)[0]
        output = output.lower()
        print (output)
        if(output.find("deleted")>=0):
            model.remove(iter)

    def AddUser(self):
        ''' Open new empty Window for UserName and Password '''
        self.ui.UserEntry.set_sensitive(True) #Used to be able to edit the User Input
        self.__OpenUsers("","","Add User")

    def EditUser(self):
        ''' Get the selected User and open a new User Window to edit the user password '''
        (model,paths)=self.ui.UsersTree.get_selection().get_selected_rows()
        iter = model.get_iter(paths[0])
        UserName = model.get_value(iter,0)
        Password = model.get_value(iter,1)

        self.ui.UserEntry.set_sensitive(False) #Used for not able to edit the UserName Input
        self.__OpenUsers(UserName,Password,"Edit "+UserName)

    def __OpenUsers(self, UserName, Password, Title):
        ''' Write the properties to the Users Window '''
        self.ui.UserOptions.set_title(Title)
        self.ui.UserEntry.set_text(UserName)
        self.ui.PasswordEntry.set_text(Password)
        self.MainWindow.ShowWindow("UserOptions")

    def ConfirmUserChanges(self):
        #Get Options from the window
        Title = self.ui.UserOptions.get_title()
        UserName = self.ui.UserEntry.get_text()
        Password = self.ui.PasswordEntry.get_text()

        if (UserName==""): #Error: Do Nothing
            return False
        if(Title.split()[0]=="Add"): #Add User
            self.ChangeUser(UserName,Password)
        else: #Edit User
            self.ChangeUser(UserName,Password)

        self.__WriteUsers() #Refresh
        self.ui.UserOptions.hide()

    def ChangeUser(self,UserName,Password):
        ''' Used to add/edit the user of the system '''
        #If the User exists then Edit the password only
        UserExists=False
        Users = Popen("sudo -S pdbedit -Lw".split(), stdout=PIPE, stdin=PIPE).communicate(self.ROOTPASS)[0]
        Users=Users.strip().split("\n")
        for item in Users:
            Users=item[:item.find(":")].strip()
            if(Users==UserName):
                UserExists=True
                print ("User Already Exists")
                break

        #Add User to the system
        if(UserExists==False):
            print "------Add User-------"
            Popen(("sudo -S useradd -r -s /bin/false "+ UserName).split(), stdin=PIPE).communicate(self.ROOTPASS)
            Popen(("sudo -S smbpasswd -n -a "+ UserName).split(), stdin=PIPE).communicate(self.ROOTPASS)[0]

        #Change Password of the User
        if(Password==self.HIDEPASS): #If no change is made to the window's password
            print ("---------Nothing Changed--------")
        elif(Password==""): #If no password is requested
            print "------Change UserName-------"
            Popen(("sudo -S smbpasswd -n -a "+ UserName).split(), stdin=PIPE).communicate(self.ROOTPASS)[0]
            print ("Password Changed to None")
        else: #If password is used
            print("-------Changing Password-------")
            smbpasswd = Popen(("sudo -S smbpasswd -s -a "+ UserName).split(), stdin=PIPE)
            smbpasswd.communicate(b'\n'.join([Password, Password]))
            print ("Password Changed to: "+Password)

#Ending
    def SaveChanges(self):
        NetBios_Name = self.ui.NetbiosName_Entry.get_text()
        WorkGroup = self.ui.Workgroup_Name.get_text()
        Null_Passwords = self.ui.AllowPassword_Switch.get_active()
        Printer_Share = self.ui.SharePrinters_Switch.get_active()
        SaveList=[]

    #Write Config from template file
        f = open("smb.conf","r")
        for line in f:
            if(line.find("----------") >= 0):
                if (Printer_Share==True):
                    line = ""
                else:
                    break
            elif(line.find("YOUR_HOSTNAME") > 0):
                line = line.replace("YOUR_HOSTNAME",NetBios_Name)
            elif(line.find("WORKGROUP") > 0):
                line = line.replace("WORKGROUP",WorkGroup)
            elif(line.find("NULL_PASS_TRUE") > 0):
                line = line.replace("NULL_PASS_TRUE",str(Null_Passwords))
            SaveList.append(line)
        f.close()

    #Write Shares
        for share in self.SharesList:
            SaveList.append("\n[" + share[0] + "]")
            SaveList.append("\n    path = "+share[1])
            if (share[2] != ""):
                SaveList.append("\n    comment = "+share[2])
            if (share[3].lower() == "public"):
                SaveList.append("\n    public = yes")
            else:
                SaveList.append("\n    valid users = " + share[3])
            SaveList.append("\n    "+share[4].lower()+" = yes\n")

    #Save the list to the config file
        f = open("/tmp/smb.conf","w")
        self.ui.ShowConfig_textview.get_buffer().set_text("")
        for item in SaveList:
            f.write(item)
            self.ui.ShowConfig_textview.get_buffer().insert(self.ui.ShowConfig_textview.get_buffer().get_end_iter(), item)

        Popen(("sudo -S mv /tmp/smb.conf "+ self.SMBFILE).split(), stdin=PIPE).communicate(self.ROOTPASS)
        Popen(("sudo -S service smbd restart").split(), stdin=PIPE).communicate(self.ROOTPASS)


class Window(WinFunc):
    '''Main Class for Signals'''
    def __init__(self):
        self.MainWindow = builder("SambaConfigWindow.glade","samba_config_window")
        self.ui = self.MainWindow.get_ui(self)

        PASSWORD = "1"
        WinFunc.Initialize(self, PASSWORD)

#Window Signals
    def on_samba_config_window_destroy(self, widget, data=None):
        Gtk.main_quit()
    def on_mnu_close_activate(self, widget, data=None):
        Gtk.main_quit()
    def on_ShareOptions_delete_event(self, widget, data=None):
        self.ui.ShareOptions.hide()
        return True
    def on_BrowseDialog_delete_event(self, widget, data=None):
        self.ui.BrowseDialog.hide()
        return True
    def on_UserOptions_delete_event(self, widget, data=None):
        self.ui.UserOptions.hide()
        return True


#Toolbar Main Buttons
    def on_SaveButton_clicked(self, widget, data=None):
        WinFunc.SaveChanges(self)

    def on_RefreshButton_clicked(self, widget, data=None):
        WinFunc.Initialize(self, self.ROOTPASS)


#Shares Tab
    def on_EditButton_clicked(self, widget, data=None):
        WinFunc.EditShares(self)

    def on_DeleteButton_clicked(self, widget, data=None):
        WinFunc.DeleteShares(self)

    def on_AddButton_clicked(self, widget, data=None):
        WinFunc.AddShares(self)

    def on_SharesTree_focus_out_event(self,widget,gpoint):
        self.ui.EditButton.set_sensitive(False)
        self.ui.DeleteButton.set_sensitive(False)
        self.ui.AddButton.set_sensitive(False)

    def on_SharesTree_focus_in_event(self,widget,gpoint):
        self.ui.EditButton.set_sensitive(True)
        self.ui.DeleteButton.set_sensitive(True)
        self.ui.AddButton.set_sensitive(True)
        WinFunc.WriteShares(self)

#Users Tab
    def on_AddUserButton_clicked(self,widget,data=None):
        WinFunc.AddUser(self)

    def on_EditUserButton_clicked(self,widget,data=None):
        WinFunc.EditUser(self)

    def on_DeleteUserButton_clicked(self,widget,data=None):
        WinFunc.DeleteUser(self)


#Shares Window
    def on_SharesCheckPublic_toggled(self, widget, data=None):
        if (self.ui.SharesCheckPublic.get_active()==True):
            self.ui.TabsNotebook.set_show_tabs(False)
        else:
            self.ui.TabsNotebook.set_show_tabs(True)

    def on_SharesButtonOK_clicked(self, widget, data=None):
        WinFunc.ConfirmShareChanges(self)

    def on_SharesButtonBrowse_clicked(self, widget, data=None):
        self.MainWindow.ShowWindow("BrowseDialog")
        Directory = self.ui.SharesEntryDirectory.get_text()
        if(Directory == ""):
            self.ui.BrowseDialog.set_current_folder("/home")
        else:
            self.ui.BrowseDialog.set_current_folder(Directory)

    def on_SharesButtonCancel_clicked(self, widget, data=None):
        self.ui.ShareOptions.hide()

#BrowseDialog Window
    def on_BrowseOK_clicked(self, widget, data=None):
        try:
            self.ui.SharesEntryDirectory.set_text(self.ui.BrowseDialog.get_current_folder())
            self.ui.BrowseDialog.hide()
        except:
            output = Popen(["notify-send", "This is not a Directory"]).communicate()

    def on_BrowseCancel_clicked(self, widget, data=None):
        self.ui.BrowseDialog.hide()

#Users Window
    def on_UserButtonOK_clicked(self, widget, data=None):
        WinFunc.ConfirmUserChanges(self)

    def on_UserButtonCancel_clicked(self, widget, data=None):
        self.ui.UserOptions.hide()

editor = Window()
Gtk.main()
