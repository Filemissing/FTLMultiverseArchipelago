---@diagnostic disable: lowercase-global
---@diagnostic disable: undefined-global
-- variables from hyperspace lua api
Hyperspace = Hyperspace
script = script
log = log
Defines = Defines
---@diagnostic enable: undefined-global
---@diagnostic enable: lowercase-global

Main = {}

function OnLoad()
    Communication.Log("Loaded successfully")
    DeathLinkSet = false
end
function OnInit(newGame)
    -- reference important classes
    Global = Hyperspace.Global.GetInstance()
    PlayerShipManager = Global:GetShipManager(0)
    PlayerShipManagerExtend = PlayerShipManager.PlayerShipManagerExtend

    CApp = Global:GetCApp()
    WorldManager = CApp.world
    StarMap = WorldManager.starMap

    if (newGame) then
        Communication.SendMessage("Started a new game")
        DeathLinkSet = false -- reset death link when starting a new run since it won't do anything
    else
        Communication.SendMessage("Loaded previous save")
    end
end

function OnTick()
    Communication.CheckMessages()
    Communication.RemoveOldMessages()
    TryApplyDeathLink()
end

function Main.OnClientMessage(cmd, args)
    if cmd == "EXIT" then
        if CApp then
            CApp:OnRequestExit()            
        end
    elseif cmd == "DEATH" then
        DeathLinkSet = true
    end
end

function TryApplyDeathLink()
    if DeathLinkSet ~= true then
        return
    end

    if PlayerShipManager ~= nil then
        PlayerShipManager:DamageHull(9999, true)
    end
end

-- handles all events that create a choicebox
function OnPostCreateChoiceBox(choiceBox, event)
    if event.eventName == "DEATH" then
        if DeathLinkSet == true then
            DeathLinkSet = false -- ignore death caused by death link and reset it's value
            return
        end
        Communication.SendMessage("DEATH")
    else
        Communication.SendMessage("CHOICE|"..event.eventName)
    end
end

-- resgister functions
script.on_load(OnLoad)
script.on_init(OnInit)
script.on_internal_event(Defines.InternalEvents.ON_TICK, OnTick)
script.on_internal_event(Defines.InternalEvents.POST_CREATE_CHOICEBOX, OnPostCreateChoiceBox)