---@diagnostic disable: lowercase-global
---@diagnostic disable: undefined-global
-- variables from hyperspace lua api
Hyperspace = Hyperspace
script = script
log = log
Defines = Defines
---@diagnostic enable: undefined-global
---@diagnostic enable: lowercase-global

function OnLoad()
    Communication.Log("Loaded successfully")
end
function OnInit(newGame)
    if (newGame) then
        Communication.SendMessage("Started a new game")
    else
        Communication.SendMessage("Loaded previous save")
    end

    -- reference important classes
    Global = Hyperspace.Global.GetInstance()
    CApp = Global:GetCApp()
    WorldManager = CApp.world
    StarMap = WorldManager.starMap
    CurrentSector = nil

end
function OnTick()
    Communication.CheckMessages()
    Communication.RemoveOldMessages()
    MonitorSector()
end

function MonitorSector()
    if CurrentSector ~= StarMap.currentSector then
        CurrentSector = StarMap.currentSector
        Communication.SendMessage("Entered sector: "..CurrentSector.description.type)
    end
end

-- handles all events that create a choicebox
function OnPostCreateChoiceBox(choiceBox, event)
    Communication.SendMessage(event.eventName)
end

-- resgister functions
script.on_load(OnLoad)
script.on_init(OnInit)
script.on_internal_event(Defines.InternalEvents.ON_TICK, OnTick)
script.on_internal_event(Defines.InternalEvents.POST_CREATE_CHOICEBOX, OnPostCreateChoiceBox)