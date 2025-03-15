from sekaibot import Node
from sekaibot.rule import StartsWith
#from sekaibot.rule import rule_at_me

startswith_rule = StartsWith("Hello world")

@startswith_rule
class HelloWorldNode(Node):

    if_startswith = startswith_rule.Param()

    """Hello, World! 示例节点。"""
    priority = 0
    async def handle(self):
        print(startswith_rule.param)
        return None
    
    
class HelloWorldNode1(Node):
    """Hello, World! 示例节点。"""
    parent = "HelloWorldNode"
    priority = 5
    async def handle(self):
        print(self.bot.config.model_dump_json(indent=4))
        return None
    
    async def rule(self):
        result = await StartsWith("hello")(self.bot, self.event, self.state)
        return True
    
class HelloWorldNode2(Node):
    """Hello, World! 示例节点。"""
    parent = "HelloWorldNode"
    priority = 2
    async def handle(self):
        pass
    
    async def rule(self):
        return True
    
class HelloWorldNode1_1(Node):
    """Hello, World! 示例节点。"""
    parent = "HelloWorldNode1"
    priority = 5
    async def handle(self):
        return None
    
    async def rule(self):
        return True
    

    