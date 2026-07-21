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
end
function OnInit(newGame)
    -- reference important classes
    Global = Hyperspace.Global.GetInstance()
    PlayerShipManager = Global:GetShipManager(0)

    CApp = Global:GetCApp()
    WorldManager = CApp.world
    CommandGui = CApp.gui
    Equipment = CommandGui.equipScreen
    StarMap = WorldManager.starMap

    if (newGame) then
        Communication.SendMessage("Started a new game")
        Hyperspace.metaVariables.DeathlinkSet = 0 -- reset death link when starting a new run since it would just be annoying
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
        Hyperspace.metaVariables.DeathlinkSet = 1
    elseif cmd == "ITEM" then
        local type = args[1]
        local id = args[2]
        local amount = args[3]

        GiveItem(type, id, amount)
    else
       Communication.Log("recieved message with unknown command '"..cmd.."' and arguments '"..args.."'")
    end
end

function GiveItem(type, id, amount)
    if type == "resource" then
        GiveResource(id, amount)
    elseif type == "augment" then
        GiveAugment(id, amount)
    elseif type == "crew" then
        GiveCrew(id, amount)
    elseif type == "sector" then
        GiveSector(id, amount)
    elseif type == "system" then
        GiveSystem(id, amount)
    elseif type == "weapon" then
        GiveWeapon(id, amount)
    elseif type == "drone" then
        GiveDrone(id, amount)
    end
end
function GiveResource(id, amount)
    if id == "scrap" then
        PlayerShipManager:ModifyScrapCount(amount, false) -- don't count as income
    elseif id == "fuel" then
        PlayerShipManager.fuel_count = PlayerShipManager.fuel_count + amount -- for some reason this can be edited directly
    elseif id == "missiles" then
        PlayerShipManager:ModifyMissileCount(amount)
    elseif id == "droneparts" then
        PlayerShipManager:ModifyDroneCount(amount)
    end
end
function GiveAugment(id, amount)
    -- both of these work but neither triggers overFull capacity, 1st is said to work properly with hidden augments if necessary (I don't think it does)

    -- PlayerShipManager:AddAugmentation(id)
    -- Equipment:AddToCargo(id)

    local bp = Hyperspace.Blueprints:GetAugmentBlueprint(id)
    Equipment:AddAugment(bp, false, true) -- working overload but doesn't handle hidden augments
end
function GiveCrew(id, amount)
    -- local blueprint = Hyperspace.Blueprints:GetCrewBlueprint(id)
    -- PlayerShipManager:AddCrewMemberFromBlueprint(blueprint, 0, true, 0, false)

    -- best option for now, just need to find a way to randomize name
    PlayerShipManager:AddCrewMemberFromString("APerson", id, false, 0, true, true)
end
function GiveSector(id, amount)
    -- use archipelaHat or add to list and manually modify choicebox

end
function GiveSystem(id, amount)
    -- only enforce limit, don't actually give system levels
    local intID = Hyperspace.ShipSystem.NameToSystemId(id)
    local system = PlayerShipManager:GetSystem(intID)
    system.maxLevel = system.maxLevel + amount
end
function GiveWeapon(id, amount)
    Equipment:AddToCargo(id)
end
function GiveDrone(id, amount)
    Equipment:AddToCargo(id)
end

function TryApplyDeathLink()
    if Hyperspace.metaVariables.DeathlinkSet ~= 1 then
        return
    end

    if PlayerShipManager ~= nil then
        PlayerShipManager:DamageHull(9999, true) -- it would be funny if this somehow doesn't kill
    end
end

-- handles all events that create a choicebox
function OnPostCreateChoiceBox(choiceBox, event)
    if event.eventName == "DEATH" then
        if Hyperspace.metaVariables.DeathlinkSet == 1 then
            Hyperspace.metaVariables.DeathlinkSet = 0 -- ignore death caused by death link and reset it's value
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