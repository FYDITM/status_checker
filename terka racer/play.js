var TRK = TRK || {};
TRK.gameplay = function(game) {};

TRK.gameplay.prototype = {
    init: function() {
        this.game.input.maxPointers = 1;
        this.game.stage.disableVisibilityChange = true;

        this.elapsed = 0;
        this.totalScore = 0;
        this.counter = 0;
        this.speed = 100;

        this.jumpForce = 0;
        this.maxJumpForce = 1500;
        this.slow = false;
        this.dash = false;
        this.dashSpeed = 300;
    },

    preload: function() {
        this.load.image('background', 'assets/background.png');
        this.load.image('soil_ground', 'assets/soil_ground.png'); //800x14
        this.load.spritesheet('racer', 'assets/racer.png', 128, 95, 6);
        this.load.spritesheet('hpbar', 'assets/hpbar.png', 153, 26, 2);

        this.load.audio('uuu', 'assets/uuu.mp3');
        this.load.audio('uu', 'assets/uu.mp3');
        this.load.audio('u', 'assets/u.mp3');

    },

    create: function() {
        this.background = this.add.tileSprite(0, 0, 1600, 640, 'background');
        this.player = this.add.sprite(0, 590, 'racer');
        this.player.health = this.player.maxHealth = 100;
        this.player.animations.add("ride", [0, 1, 2, 3], 4, true, true);
        this.player.animations.add("jump", [4], 4, false, true);
        this.player.animations.add("fall", [5], 4, false, true);

        this.hpbars = this.add.group();
        this.hpbarEmpty = this.add.sprite(this.game.width - 170, 10, "hpbar", 1);
        this.hpbarFull = this.add.sprite(this.hpbarEmpty.x, this.hpbarEmpty.y, "hpbar", 0);
        this.hpRect = new Phaser.Rectangle(0, 0, this.hpbarEmpty.width, this.hpbarEmpty.height);

        this.u = this.add.audio('u');
        this.uu = this.add.audio('uu');
        this.uuu = this.add.audio('uuu');
        //this.sound.setDecodedCallback([this.uu, this.uuu], this.ready, this);

        this.physics.startSystem(Phaser.Physics.ARCADE);
        this.physics.enable(this.player);
        this.player.body.gravity.y = 1400;
        this.player.body.collideWorldBounds = true;
        this.player.anchor.set(0.5, 1);
        this.platforms = this.add.group();
        this.platforms.enableBody = true;
        this.ground = this.add.tileSprite(0, 590, 1600, 14, 'soil_ground');
        this.physics.enable(this.ground);
        this.ground.body.immovable = true;

        cursors = this.input.keyboard.createCursorKeys();
        this.scoreText = this.add.text(10, 20, this.totalScore);
        new Platform(this);
        console.log(this.hpRect);
        console.log(this.hpbarFull.height);
    },


    update: function() {
        this.scoreText.destroy();
        this.scoreText = this.add.text(10, 20, `punkty: ${Math.trunc(this.totalScore)}`);

        this.physics.arcade.collide(this.player, this.ground);
        this.physics.arcade.collide(this.player, this.platforms, this.collide, null, this);
        this.move();
        if (cursors.right.isDown) {
            this.dash = true;
        } else if (this.dash) {
            this.dash = false;
        }

        if (cursors.left.isDown) {
            this.slow = true;
        } else if (this.slow) {
            this.slow = false;
        }

        if ((cursors.up.isDown || this.input.keyboard.isDown(Phaser.KeyCode.SPACEBAR)) && this.player.body.touching.down) {
            this.jumpForce += this.jumpForce > this.maxJumpForce ? 0 : 30;
        } else if (this.player.body.touching.down && this.jumpForce > 0) {
           this.jump();
        }
        if (this.player.body.velocity.y < -50 && !this.player.body.touching.down) {
            this.player.animations.play('jump');
        } else if (this.player.body.velocity.y > 0 && !this.player.body.touching.down) {
            this.player.animations.play('fall');
        }

    },

    ready: function(){

    },

    jump: function() {
         this.player.body.velocity.y = -this.jumpForce;
            if (this.jumpForce > this.maxJumpForce * 0.7) {
                this.uuu.play();
            } else if (this.jumpForce > this.maxJumpForce * 0.4) {
                this.uu.play();
            } else {
                this.u.play();
            }
            this.jumpForce = 0;
    },

    move: function() {
        var currSpeed = this.currentSpeed();
        this.player.animations.play('ride', currSpeed / 50, false);
        this.background.autoScroll(-currSpeed / 2, 0);
        this.ground.autoScroll(-currSpeed, 0);

        this.platforms.forEach(function(x) {
            if (x.x + x.width < 0) {
                x.destroy();
            } else {
                x.body.velocity.x = -currSpeed;
            }
        });

        var step = currSpeed / 1000;
        this.speed += step / 3;
        this.elapsed += step;
        this.totalScore += step;
        this.counter++;

        if (this.counter >= 100 && this.rnd.frac() < 0.4) {
            new Platform(this);
            this.counter = 0;
        }
    },

    collide: function() {
        this.onFloor();
        if (!this.player.body.touching.down || this.onFloor()) {
            this.damagePlayer();
        }
    },

    stop: function() {
        this.background.stopScroll();
        this.ground.stopScroll();
        this.player.animations.play('ride');
        this.player.animations.stop('ride');
    },

    onFloor: function() {
        return this.player.bottom == 590;
    },

    damagePlayer: function() {
        this.player.damage(2);
        this.hpRect.width = Math.floor((this.player.health / this.player.maxHealth) * this.hpbarEmpty.width);
        this.hpbarFull.crop(this.hpRect);
    },

    currentSpeed: function() {
        var c = this.dash ? 2 : (this.slow ? 0.5 : 1);
        return this.speed * c;
    },

    checkFreeSpace: function(rect) {
        var result = true;
        this.platforms.forEach(function(el) {
            if (Phaser.Rectangle.intersects(rect, el)) {
                result = false;
            }
        });
        return result;
    }
};



var Platform = function(game) {
    this.maxWidth = 400;
    this.maxHeight = 100;
    this.minWidth = 100;
    this.minHeight = 30;
    var width = game.rnd.integerInRange(this.minWidth, this.maxWidth);
    var height = game.rnd.integerInRange(this.minHeight, this.maxHeight);
    var x = game.world.bounds.width + 100;
    var y = game.rnd.integerInRange(game.world.height / 2, game.world.height - 50);
    if (!game.checkFreeSpace(new Phaser.Rectangle(x, y, width, height))) {

        return;
    }
    this.sprite = game.add.sprite(x, y, "soil_ground");
    this.sprite.width = width;
    this.sprite.height = height;
    game.physics.enable(this.sprite, Phaser.Physics.ARCADE);
    game.platforms.add(this.sprite);
    this.sprite.body.immovable = true;
};